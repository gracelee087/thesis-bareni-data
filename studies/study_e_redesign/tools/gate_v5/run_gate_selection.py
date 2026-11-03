"""Gate API runner, isolated from evaluator history. Defaults to offline checks."""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import math
import random
import re
import time
from datetime import datetime, timezone
from pathlib import Path

from gate_contract import GateInput, validate_output
from request_schema import provider_schema, normalize_wire

STUDY = Path(__file__).resolve().parents[2]
CONFIG = STUDY / '58_GATE_RUN_CONFIG_V5.json'
WORK = STUDY / 'private/gate_v5'
DATA = STUDY / 'private/gate_v5'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def utc():
    return datetime.now(timezone.utc).isoformat()


def save_new(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')


def source_paths():
    return [CONFIG, STUDY/'53_GATE_PROMPT_V5.md', STUDY/'52_GATE_V5_SEMANTIC_REPAIR_PLAN.md',
            STUDY/'54_GATE_V5_AUTHOR_RATING_PACKET.md', STUDY/'56_GATE_V5_USER_RATINGS_RAW.md',
            STUDY/'57_GATE_V5_AUTHOR_REFERENCE_RECEIPT.md', STUDY/'59_GATE_V5_EXECUTION_PREPARATION.md',
            STUDY/'34_GATE_BOUNDARY_AND_AUDIT_REVIEW.md', STUDY/'36_GATE_EXECUTION_AUTHORIZATION.md',
            DATA/'neutral_items_draft.json', DATA/'candidate_inputs_draft.json',
            DATA/'prompt_baseline_freeze.json', DATA/'preparation_receipt.json',
            DATA/'author_ratings_parsed.json', DATA/'author_reference_freeze.json',
            STUDY/'private/gate_v4/freeze.json', STUDY/'private/gate_v4/smoke_receipt.json',
            *sorted((STUDY/'private/gate_v4/results').glob('*.json')),
            *sorted(Path(__file__).parent.glob('*.py'))]


def verify_prepared_references():
    for filename in ('prompt_baseline_freeze.json','preparation_receipt.json','author_reference_freeze.json'):
        receipt=read(DATA/filename)
        for field in ('sha256','source_sha256','artifact_sha256'):
            for name,expected in receipt.get(field,{}).items():
                path=(STUDY/name).resolve()
                if not path.is_relative_to(STUDY.resolve()) or digest(path)!=expected:
                    raise RuntimeError('v5 prepared/reference source changed: '+name)


def versions():
    return {name: importlib.metadata.version(name) for name in ('openai','anthropic','pydantic','jsonschema')}


def system_prompt():
    text=(STUDY/'53_GATE_PROMPT_V5.md').read_text(encoding='utf-8')
    return text.split('## System prompt\n',1)[1].split('## User payload template',1)[0].strip()


def assemble():
    """Read only prepared neutral inputs; never author scores/construction intentions."""
    prepared=read(DATA/'candidate_inputs_draft.json')
    if prepared['system']!=system_prompt():
        raise RuntimeError('v5 prepared prompt mismatch')
    inputs=prepared['inputs']
    if len(inputs)!=24 or {i['request']['item_id'] for i in inputs}!={f'GATE-BLIND-{n:03}' for n in range(101,125)}:
        raise RuntimeError('expected new v5 neutral items 101-124')
    for item in inputs:
        request=GateInput.model_validate(item['request'])
        if json.loads(item['user'].split('\n\n',1)[1])['assessment_input']!=request.model_dump():
            raise RuntimeError('v5 payload/input mismatch')
    return inputs


def request_kwargs(candidate, system, user, max_tokens, request):
    common = {'model':candidate['model']}
    request=GateInput.model_validate(request)
    # Bind the exact neutral input to the transmitted schema; never infer from author answers.
    payload=json.loads(user.split('\n\n',1)[1])['assessment_input']
    if payload!=request.model_dump():
        raise ValueError('request/schema input mismatch')
    schema = provider_schema(candidate['provider'],request)
    if candidate['provider']=='openai':
        return dict(common,input=[{'role':'system','content':system},{'role':'user','content':user}],
                    max_output_tokens=max_tokens,store=False,
                    text={'format':{'type':'json_schema','name':'study_e_gate','strict':True,'schema':schema}})
    return dict(common,system=system,messages=[{'role':'user','content':user}],max_tokens=max_tokens,
                output_config={'format':{'type':'json_schema','schema':schema}})


def usage_and_cost(provider, response, rates):
    def count(value):
        if type(value) is not int or value<0:
            raise ValueError('usage must contain nonnegative integers')
        return value
    u=response['usage']
    if provider=='openai':
        total=count(u['input_tokens']); cached=count((u.get('input_tokens_details') or {}).get('cached_tokens',0))
        write=0; output=count(u['output_tokens'])
        reasoning=count((u.get('output_tokens_details') or {}).get('reasoning_tokens',0))
    else:
        cached=count(u.get('cache_read_input_tokens',0) or 0)
        write=count(u.get('cache_creation_input_tokens',0) or 0)
        total=count(u['input_tokens'])+cached+write; output=count(u['output_tokens']); reasoning=None
    if min(total,cached,write,output)<0 or total<cached+write:
        raise ValueError('invalid provider usage')
    cost=((total-cached-write)*rates['input']+cached*rates['cached_input']+
          write*rates['cache_write_input']+output*rates['output'])/1e6
    return dict(input_tokens=total,cached_input_tokens=cached,cache_write_input_tokens=write,
                output_tokens=output,reasoning_tokens=reasoning),round(cost,8)


def money(value):
    if type(value) not in (int,float) or not math.isfinite(value) or value<0:
        raise ValueError('invalid ledger charge')
    return value


def stop_required(records):
    previous={}
    for record in records:
        status=record['terminal_status']; candidate=record['candidate_id']
        if status in ('transport_failure','usage_failure','model_mismatch','response_failure'):
            return True
        bad=status in ('validation_failure','input_problem')
        if bad and previous.get(candidate,False): return True
        previous[candidate]=bad
    return False


def load_ledger(root, frozen, freeze_hash):
    order={(row['candidate_id'],row['item_id']):n for n,row in enumerate(frozen['schedule'])}
    records=[]; seen=set()
    for path in sorted((root/'results').glob('*.json')):
        record=read(path); pair=(record['candidate_id'],record['item_id'])
        if pair not in order or pair in seen or path.stem!='__'.join(pair):
            raise RuntimeError('unexpected, duplicate or misnamed ledger record')
        if record['freeze_sha256']!=freeze_hash:
            raise RuntimeError('mixed freeze records')
        if record['terminal_status'] not in ('success','validation_failure','input_problem',
                   'transport_failure','usage_failure','model_mismatch','response_failure'):
            raise RuntimeError('unknown terminal status')
        attempts=record['attempts']
        if not attempts or [a['attempt'] for a in attempts]!=list(range(1,len(attempts)+1)):
            raise RuntimeError('invalid attempt ledger')
        charged=sum(money(a['budget_charge_usd']) for a in attempts)
        if not math.isclose(money(record['budget_charge_usd']),charged,rel_tol=0,abs_tol=1e-9):
            raise RuntimeError('attempt charge mismatch')
        seen.add(pair); records.append(record)
    records.sort(key=lambda row:order[(row['candidate_id'],row['item_id'])])
    if [order[(r['candidate_id'],r['item_id'])] for r in records]!=list(range(len(records))):
        raise RuntimeError('ledger is not a contiguous schedule prefix')
    for path in (root/'started').glob('*.json'):
        if not (root/'results'/path.name).exists():
            raise RuntimeError('interrupted request needs reconciliation before resume: '+path.stem)
    return records


def reserve(candidate, kwargs, max_tokens):
    # Conservative local estimate, NOT a provider-certified billing upper bound.
    input_estimate=len(json.dumps(kwargs,ensure_ascii=False).encode('utf-8'))+4096
    return (input_estimate*max(candidate['input'],candidate['cache_write_input'])+
            max_tokens*candidate['output'])/1e6


def preflight():
    verify_prepared_references()
    config=read(CONFIG); inputs=assemble(); system=system_prompt()
    schedule=[(c['candidate_id'],i['request']['item_id']) for c in config['candidates'] for i in inputs]
    random.Random(config['seed']).shuffle(schedule)
    if len(schedule)!=48 or len(set(schedule))!=48:
        raise ValueError('schedule must have exactly 48 unique pairs')
    costs={}; request_hashes={}
    for c in config['candidates']:
        costs[c['candidate_id']]=0
        for item in inputs:
            kwargs=request_kwargs(c,system,item['user'],config['max_output_tokens'],item['request'])
            costs[c['candidate_id']]+=reserve(c,kwargs,config['max_output_tokens'])
            key=c['candidate_id']+'__'+item['request']['item_id']
            request_hashes[key]=hashlib.sha256(json.dumps(kwargs,ensure_ascii=False,
                sort_keys=True,separators=(',',':')).encode('utf-8')).hexdigest()
    review=dict(config['review'])
    if (WORK/'smoke_receipt.json').exists():
        receipt=read(WORK/'smoke_receipt.json')
        review['paid_smoke_passed']=(receipt.get('all_valid') is True and
            receipt.get('source_sha256')=={str(p.relative_to(STUDY)):digest(p) for p in source_paths()})
    return dict(prepared_pairs=48,unique_pairs=48,validated_inputs=24,paid_calls=0,
                sdk_versions=versions(),proposed_stage_cap_usd=config['proposed_stage_cap_usd'],
                conservative_single_attempt_estimate_usd=costs,
                blockers=[k for k,v in review.items() if v is not True],
                request_sha256=request_hashes,
                source_sha256={str(p.relative_to(STUDY)):digest(p) for p in source_paths()},
                schedule=[{'candidate_id':c,'item_id':i} for c,i in schedule])


def create_clients(config):
    from dotenv import load_dotenv
    from openai import OpenAI
    from anthropic import Anthropic
    load_dotenv(STUDY.parents[1]/'.env',override=False)
    return {'openai':OpenAI(max_retries=0,timeout=config['request_timeout_seconds']),
            'anthropic':Anthropic(max_retries=0,timeout=config['request_timeout_seconds'])}


def verify_frozen():
    frozen=read(WORK/'freeze.json'); current=preflight()
    if current['blockers'] or current['source_sha256']!=frozen['source_sha256']:
        raise RuntimeError('unresolved review or changed frozen sources')
    if (current['sdk_versions']!=frozen['sdk_versions'] or current['schedule']!=frozen['schedule'] or
            current['request_sha256']!=frozen['request_sha256']):
        raise RuntimeError('runtime or schedule changed')
    from gate_lifecycle import verify_smoke
    verify_smoke(current)
    return frozen


def validate_response(response, provider, candidate, request):
    raw=response.model_dump(mode='json')
    result=dict(provider_response=raw,raw_text=None,usage=None,cost_usd=None,rating=None,
                status='usage_failure',error=None)
    try:
        result['usage'],result['cost_usd']=usage_and_cost(provider,raw,candidate)
    except (KeyError,TypeError,ValueError,OverflowError) as exc:
        result['error']=type(exc).__name__
        return result
    try:
        text=(response.output_text if provider=='openai' else ''.join(
            b.text for b in response.content if getattr(b,'type',None)=='text'))
        if not isinstance(text,str): raise TypeError('response text is not a string')
        result['raw_text']=text
    except (AttributeError,TypeError,ValueError) as exc:
        result.update(status='response_failure',error=type(exc).__name__)
        return result
    actual=raw.get('model','')
    allowed=(actual==candidate['model'] or (provider=='openai' and
        re.fullmatch(re.escape(candidate['model'])+r'-\d{4}-\d{2}-\d{2}',actual) is not None))
    if not allowed:
        result.update(status='model_mismatch',error='unexpected returned model')
        return result
    stop=raw.get('status') if provider=='openai' else raw.get('stop_reason')
    result['stop_reason']=stop
    try:
        if stop!=('completed' if provider=='openai' else 'end_turn'):
            raise ValueError('incomplete/refused response: '+str(stop))
        request_obj=GateInput.model_validate(request)
        normalized=normalize_wire(text,request_obj)
        parsed=validate_output(normalized,request_obj)
        result.update(status='success' if parsed.assessment_status=='assessed' else 'input_problem',
                      rating=parsed.model_dump())
    except ValueError as exc:
        result.update(status='validation_failure',error=str(exc))
    return result


def run(confirmation):
    if confirmation!='RUN-STUDY-E-GATE-48':
        raise RuntimeError('explicit paid confirmation required')
    frozen=verify_frozen(); config=read(CONFIG)
    # Fail closed until a future approved freeze includes the smoke ledger.
    smoke=read(WORK/'smoke_receipt.json')
    if not smoke['all_valid'] or digest(WORK/'smoke_receipt.json')!=frozen['smoke_receipt_sha256']:
        raise RuntimeError('missing or changed smoke receipt')
    if (WORK/'diagnostic_stop.json').exists():
        raise RuntimeError('persistent diagnostic stop requires documented reconciliation')
    inputs={i['request']['item_id']:i for i in assemble()}
    candidates={c['candidate_id']:c for c in config['candidates']}; system=system_prompt()
    results=WORK/'results'; results.mkdir(parents=True,exist_ok=True)
    records=load_ledger(WORK,frozen,digest(WORK/'freeze.json'))
    if stop_required(records):
        raise RuntimeError('ledger requires diagnostic stop even without stop marker')
    spend=money(smoke.get('budget_charge_usd',smoke['cost_usd']))+sum(money(r['budget_charge_usd']) for r in records)
    clients=create_clients(config)
    for index,row in enumerate(frozen['schedule'],1):
        key=f"{row['candidate_id']}__{row['item_id']}"
        dest=results/(key+'.json'); marker=WORK/'started'/(key+'.json')
        if dest.exists(): continue
        if marker.exists():
            raise RuntimeError('interrupted request needs reconciliation before resume: '+key)
        c=candidates[row['candidate_id']]; item=inputs[row['item_id']]
        kwargs=request_kwargs(c,system,item['user'],config['max_output_tokens'],item['request'])
        upper=reserve(c,kwargs,config['max_output_tokens'])
        if spend+upper*config['max_attempts']>config['proposed_stage_cap_usd']:
            raise RuntimeError('next-call reservation exceeds proposed stage cap')
        save_new(marker,dict(started_at=utc(),reserved_usd=upper*config['max_attempts'],
                            candidate_id=c['candidate_id'],item_id=row['item_id'],request=kwargs))
        attempts=[]; terminal='transport_failure'; rating=None
        for attempt in range(1,config['max_attempts']+1):
            start=time.perf_counter(); started=utc(); provider=c['provider']
            try:
                response=(clients[provider].responses.create(**kwargs) if provider=='openai'
                          else clients[provider].messages.create(**kwargs))
            except Exception as exc:
                status=getattr(exc,'status_code',None)
                attempts.append(dict(attempt=attempt,started_at=started,latency_ms=round((time.perf_counter()-start)*1000),
                                     status='transport_error',error_kind=type(exc).__name__,http_status=status,
                                     error_body=getattr(exc,'body',None),
                                     usage=None,cost_usd=None,budget_charge_usd=upper))
                # Unknown usage is reserved, never silently counted as free.
                if status in config['retryable_statuses'] and attempt<config['max_attempts']:
                    time.sleep(min(2**attempt,8)); continue
                break
            checked=validate_response(response,provider,c,item['request'])
            terminal=checked['status']; rating=checked.pop('rating'); cost=checked['cost_usd']
            attempts.append(dict(attempt=attempt,started_at=started,latency_ms=round((time.perf_counter()-start)*1000),
                                 **checked,budget_charge_usd=cost if cost is not None else upper))
            break
        record=dict(candidate_id=c['candidate_id'],item_id=row['item_id'],requested_model=c['model'],
                    freeze_sha256=digest(WORK/'freeze.json'),terminal_status=terminal,rating=rating,attempts=attempts,
                    budget_charge_usd=sum(a['budget_charge_usd'] for a in attempts))
        save_new(dest,record); spend+=record['budget_charge_usd']
        print(f'completed_schedule_index={index}/48 status={terminal} budget_charge_usd={spend:.6f}',flush=True)
        records.append(record)
        recent=[r for r in records if r['candidate_id']==c['candidate_id']][-2:]
        repeated=(len(recent)==2 and all(r['terminal_status'] in
                  ('validation_failure','input_problem') for r in recent))
        if terminal in ('transport_failure','usage_failure','model_mismatch','response_failure') or repeated:
            save_new(WORK/'diagnostic_stop.json',dict(created_at=utc(),key=key,
                     reason=terminal,repeated_contract_failure=repeated))
            raise RuntimeError('stopped for diagnosis; terminal record preserved')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('command',choices=['preflight','prepare','run'])
    parser.add_argument('--confirm',default='')
    args=parser.parse_args()
    if args.command=='run': run(args.confirm); return
    result=preflight()
    if args.command=='prepare':
        save_new(WORK/'prepared_draft.json',dict(created_at=utc(),**result))
    # Do not print neutral texts, answers, credentials, or candidate judgments.
    print(json.dumps({k:v for k,v in result.items() if k not in ('source_sha256','schedule','request_sha256')},indent=2))


if __name__=='__main__': main()
