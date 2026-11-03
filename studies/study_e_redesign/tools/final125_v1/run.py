"""Prospective Study E: real LangGraph nodes, Langfuse generations, immutable calls.

No live execution is possible before a matching registration receipt is recorded.
LangGraph controls role transitions; persisted API results make graph replay idempotent.
"""
from __future__ import annotations
import argparse
import copy
import difflib
import importlib.util
import json
import os
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextvars import ContextVar
from pathlib import Path
from typing import TypedDict, Any
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from preparation import S, ROOT, W, read, put, digest, prepare
from defects import mutate
from telemetry import Telemetry
import pricing

spec = importlib.util.spec_from_file_location('final_long_contracts', S/'tools/long125_v2/run.py')
adapter = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = adapter
spec.loader.exec_module(adapter)
p, rt = adapter.p, adapter.rt
p.W = W
rt.W = W
sha = rt.sha


class State(TypedDict, total=False):
    task: dict
    register: list
    memory_parent: str | None
    work: dict
    planner: dict
    researcher: dict
    selected: list
    planner_key: str
    researcher_key: str
    writer_key: str
    draft_key: str
    first: dict
    draft: dict
    gate_payload: dict
    initial_gate: dict
    assessment: dict
    gate_key: str
    critique: dict
    critique_key: str
    cycle: int
    cycles: list
    initial_eval: dict
    final_eval: dict
    initial_eval_key: str
    final_eval_key: str
    evaluation_reused: bool
    result: dict


def build_graph(runner):
    graph = StateGraph(State)
    def planner(s):
        t = s['task']; payload = p.planner_input(t, s['register'])
        value, key = runner.call(t['task_id']+'_planner', 'planner', payload,
                                 [s['memory_parent']] if s.get('memory_parent') else [])
        ids = {x['lesson_id'] for x in value['selected_lessons']}
        return dict(planner=value, planner_key=key,
                    selected=[x for x in s['register'] if x['lesson_id'] in ids], cycles=[], cycle=0)
    def researcher(s):
        t = s['task']; payload = p.research_input(t, s['planner'], s['selected'])
        value, key = runner.call(t['task_id']+'_researcher','researcher',payload,[s['planner_key']])
        work = copy.deepcopy(t); work['research'] = payload
        return dict(researcher=value, researcher_key=key, work=work)
    def writer(s):
        payload = p.production(s['work'],'writer',plan=s['planner'],ledger=s['researcher'])
        payload['fixed_plan'].append('Only Planner-selected lessons (guidance, not evidence): '+json.dumps(s['selected'],ensure_ascii=False))
        value, key = runner.call(s['task']['task_id']+'_writer','writer',payload,[s['planner_key'],s['researcher_key']])
        return dict(first=value,draft=value,writer_key=key,draft_key=key)
    def load_original(s):
        t = s['task']; original = read(W/'tasks'/f"{t['source_task_id']}.json")
        work = copy.deepcopy(next(x for x in runner.plan['tasks'] if x['task_id']==t['source_task_id']))
        work['research'] = p.research_input(work,original['planner'],original['selected_lessons'])
        return dict(work=work,planner=original['planner'],researcher=original['researcher'],selected=original['selected_lessons'],
                    planner_key=original['planner_key'],researcher_key=original['researcher_key'],writer_key=original['writer_key'],
                    first=t['initial'],draft=t['initial'],draft_key=original['writer_key'],cycles=[],cycle=0)
    def gate_initial(s):
        payload = rt.gate_input(s['work'],s['draft'],f"GATE-BLIND-{s['task']['index']:03}",runner.plan['templates']['gate']['rules'])
        value,key = runner.call(s['task']['task_id']+'_gate0','gate',payload,[s['draft_key']])
        return dict(gate_payload=payload,initial_gate=value,assessment=value,gate_key=key)
    def critic(s):
        cycle=s['cycle']+1
        payload=rt.critic_input(s['work'],s['draft'],s['assessment'],s['gate_payload'],f"E-CRIT-BLIND-{s['task']['index']:03}-{cycle}")
        value,key=runner.call(s['task']['task_id']+f'_critic{cycle}','critic',payload,[s['draft_key'],s['gate_key']])
        return dict(cycle=cycle,critique=value,critique_key=key)
    def optimizer(s):
        payload=p.production(s['work'],'optimizer',draft=s['draft'],repairs=s['critique'],cycle=s['cycle'])
        payload['fixed_critique'].append('Preserve original Planner guidance and Researcher restrictions: '+json.dumps(dict(plan=s['planner'],ledger=s['researcher']),ensure_ascii=False))
        value,key=runner.call(s['task']['task_id']+f"_optimizer{s['cycle']}",'optimizer',payload,[s['draft_key'],s['critique_key'],s['researcher_key']])
        return dict(draft=value,draft_key=key)
    def gate_final(s):
        payload=rt.gate_input(s['work'],s['draft'],f"GATE-BLIND-{s['task']['index']:03}",runner.plan['templates']['gate']['rules'])
        value,key=runner.call(s['task']['task_id']+f"_gate{s['cycle']}",'gate',payload,[s['draft_key']])
        return dict(gate_payload=payload,assessment=value,gate_key=key,
                    cycles=s['cycles']+[dict(cycle=s['cycle'],critique=s['critique'],gate=value,draft=s['draft'],gate_key=key)])
    def evaluate_initial(s):
        payload=rt.evaluator_input(s['work'],s['first'],f"EVAL-BLIND-{s['task']['index']:03}")
        value,key=runner.call(s['task']['task_id']+'_eval_initial','evaluator',payload,[s['writer_key']])
        return dict(initial_eval=value,initial_eval_key=key)
    def evaluate_final(s):
        same=all(s['first'][k]==s['draft'][k] for k in ('title','body'))
        if same: value,key=s['initial_eval'],s['initial_eval_key']
        else:
            payload=rt.evaluator_input(s['work'],s['draft'],f"EVAL-BLIND-{s['task']['index']:03}")
            value,key=runner.call(s['task']['task_id']+'_eval_final','evaluator',payload,[s['draft_key']])
        return dict(final_eval=value,final_eval_key=key,evaluation_reused=same)
    def production_checkpoint(s):
        t=s['task']
        path=W/'production'/f"{t['task_id']}.json"
        if path.exists():
            saved=read(path)
            if saved['final_key']!=s['draft_key'] or saved['final_gate_key']!=s['gate_key']:
                raise RuntimeError('Completed production changed on resume')
            return {}
        result=dict(task_id=t['task_id'],batch_id=t['batch_id'],condition=t['condition'],source_task_id=t.get('source_task_id'),
                    topic=s['work']['topic']['abstract_topic'],status='complete',execution_status='complete',
                    operational_route='needs_human_review' if s['assessment']['defects'] else 'release_candidate',
                    initial=s['first'],final=s['draft'],initial_gate=s['initial_gate'],final_gate=s['assessment'],cycles=s['cycles'],
                    measurement_status='pending',planner=s['planner'],researcher=s['researcher'],
                    selected_lessons=s['selected'],register_sha256=sha(s['register']),
                    planner_key=s['planner_key'],researcher_key=s['researcher_key'],writer_key=s['writer_key'],
                    final_key=s['draft_key'],final_gate_key=s['gate_key'],production_completed_at=rt.utc(),
                    orchestration='LangGraph StateGraph',telemetry='Langfuse + immutable local attempts')
        put(path,result)
        return {}
    def record(s):
        t=s['task'];result=read(W/'production'/f"{t['task_id']}.json")
        result.update(initial_eval=s['initial_eval'],final_eval=s['final_eval'],evaluation_reused=s['evaluation_reused'],
                      evaluation_keys=[s['initial_eval_key'],s['final_eval_key']],measurement_status='complete',completed_at=rt.utc())
        put(W/'tasks'/f"{t['task_id']}.json",result)
        return dict(result=result)
    nodes=dict(planner=planner,researcher=researcher,writer=writer,load_original=load_original,
               gate_initial=gate_initial,critic=critic,optimizer=optimizer,gate_final=gate_final,
               production_checkpoint=production_checkpoint,evaluate_initial=evaluate_initial,evaluate_final=evaluate_final,record=record)
    for name,fn in nodes.items(): graph.add_node(name,fn)
    graph.add_conditional_edges(START,lambda s:'planner' if s['task']['condition']=='natural' else 'load_original',
                                {'planner':'planner','load_original':'load_original'})
    for a,b in [('planner','researcher'),('researcher','writer'),('writer','gate_initial'),('load_original','gate_initial'),
                ('gate_initial','critic'),('critic','optimizer'),('optimizer','gate_final'),
                ('production_checkpoint','evaluate_initial'),('evaluate_initial','evaluate_final'),('evaluate_final','record'),('record',END)]:graph.add_edge(a,b)
    graph.add_conditional_edges('gate_final',lambda s:'critic' if s['assessment']['defects'] and s['cycle']<runner.plan['max_refinements'] else 'production_checkpoint',
                                {'critic':'critic','production_checkpoint':'production_checkpoint'})
    return graph.compile(checkpointer=InMemorySaver(),name='Study E final task')


class Runner(p.Runner):
    def __init__(self,plan,clients,telemetry):
        self.pricing=pricing.load_pricing()
        pricing.validate_plan(plan,self.pricing)
        self.plan=plan;self.clients=clients;self.lock=threading.Lock();self.freeze=digest(W/'execution_plan.json')
        self.records=[];self.charge=plan['prior_budget_charge_usd'];self.inflight=0
        for path in sorted((W/'started').glob('*.json')):
            dest=W/'results'/path.name
            if not dest.exists():
                start=read(path);metadata=start.get('metadata',{})
                put(dest,dict(key=start['key'],role=start['role'],status='interrupted_unknown',
                              output=None,usage=None,cost_usd=None,budget_charge_usd=start['reserved_usd'],
                              unknown_cost_reservation_usd=start['reserved_usd'],created_at=start['created_at'],
                              metadata=metadata,task_id=metadata.get('task_id'),batch_id=metadata.get('batch_id'),
                              cohort=metadata.get('cohort'),freeze_sha256=self.freeze))
            row=read(dest);self.records.append(row);self.charge+=row['budget_charge_usd']
        self.telemetry=telemetry; self.abort=threading.Event(); self.context=ContextVar('final_attempt_metadata',default={})
        self.pacing=threading.Lock(); self.next_request={}; self.graph=build_graph(self)

    def task(self,t,register=None,memory_parent=None):
        path=W/'tasks'/f"{t['task_id']}.json"
        if path.exists():return read(path)
        metadata=dict(task_id=t['task_id'],batch_id=t['batch_id'],condition=t['condition'],
                      cohort='natural' if t['condition']=='natural' else 'mixed')
        if t['condition']!='natural':metadata['input_manifest_sha256']=digest(W/'mixed_inputs.json')
        token=self.context.set(metadata)
        try:
            with self.telemetry.task(t['task_id'],metadata):
                out=self.graph.invoke(dict(task=t,register=register or [],memory_parent=memory_parent),
                                      config=dict(configurable=dict(thread_id=t['task_id']+'-'+str(time.time_ns())),recursion_limit=40))
        except Exception:
            self.abort.set()
            raise
        finally:self.context.reset(token)
        return out['result']

    def _pace(self,provider):
        while True:
            if self.abort.is_set():raise rt.StopRun('operational_abort')
            with self.pacing:
                delay=self.next_request.get(provider,0)-time.monotonic()
                if delay<=0:
                    self.next_request[provider]=time.monotonic()+self.plan['minimum_provider_interval_seconds']
                    return
            self.abort.wait(min(delay,2))

    def once(self,key,role,payload,parents):
        if self.abort.is_set():raise rt.StopRun('operational_abort')
        if role=='evaluator':
            kw=copy.deepcopy(payload['request']); c=pricing.candidate(role,self.pricing)
        else:
            template=self.plan['templates'][role];c=template['candidate'];kw=rt.request_for(role,payload,template)
        pricing.validate_date(self.pricing)
        if c['provider']=='openai':kw['service_tier']='default'
        reserved=pricing.reserve(c['model'],kw,self.pricing)
        self._pace(c['provider'])
        metadata=copy.deepcopy(self.context.get())
        with self.lock:
            if len(self.records)+self.inflight>=self.plan['max_calls']:raise rt.StopRun('call_limit')
            if self.charge+reserved>self.plan['cap_usd']:raise rt.StopRun('budget_limit')
            for parent in parents:
                if read(W/'results'/f'{parent}.json')['status']!='success':raise RuntimeError('Invalid parent '+parent)
            start=dict(created_at=rt.utc(),key=key,role=role,payload=payload,request=kw,candidate=c,reserved_usd=reserved,
                       freeze_sha256=self.freeze,request_sha256=sha(kw),metadata=metadata,
                       parent_sha256={x:digest(W/'results'/f'{x}.json') for x in parents})
            put(W/'started'/f'{key}.json',start);self.charge+=reserved;self.inflight+=1
        row=dict(status='transport_failure',usage=None,cost_usd=None,output=None,raw_text=None,provider_response=None)
        began=time.perf_counter()
        with self.telemetry.attempt(key,role,payload,c,kw,metadata) as observation:
            try:
                if role=='evaluator':response=self.clients['google'].models.generate_content(**kw)
                elif c['provider']=='openai':response=self.clients['openai'].responses.create(**kw)
                else:response=self.clients['anthropic'].messages.create(**kw)
                raw=response.model_dump(mode='json');row['provider_response']=raw
                if role=='evaluator':row.update(rt.check_evaluator(response,payload['item']))
                elif role=='gate':
                    checked=rt.api.validate_response(response,c['provider'],c,payload);row.update(checked);row['output']=checked['rating']
                else:
                    row['status']='usage_failure';row['usage'],row['cost_usd']=rt.api.usage_and_cost(c['provider'],raw,c)
                    actual=raw.get('model','')
                    if not (actual==c['model'] or (c['provider']=='openai' and re.fullmatch(re.escape(c['model'])+r'-\d{4}-\d{2}-\d{2}',actual))):raise rt.StopRun('model_mismatch')
                    stop=raw.get('status') if c['provider']=='openai' else raw.get('stop_reason')
                    row['raw_text']=response.output_text if c['provider']=='openai' else ''.join(b.text for b in response.content if b.type=='text')
                    row['status']='validation_failure'
                    if stop!=('completed' if c['provider']=='openai' else 'end_turn'):raise ValueError('incomplete_response')
                    row['output']=rt.parse(role,row['raw_text'],payload)
                    if role=='critic':
                        required=set(rt.cm.target_ids(payload));covered={x for r in row['output']['repairs'] for x in r['target_ids']}
                        if not required<=covered:raise ValueError('unaddressed_gate_defect')
                    if role=='memory':rt.project(row['output'],payload)
                    row.update(status='success',stop_reason=stop)
            except Exception as exc:
                row.update(error_kind=type(exc).__name__,http_status=getattr(exc,'status_code',None))
                if isinstance(exc,ValueError):row['validation_detail']=self.telemetry.sanitize(str(exc)[:800])
                if isinstance(exc,rt.StopRun):row['status']=str(exc)
                # Store only provider error codes; messages/headers may contain secrets.
                error=getattr(exc,'body',None)
                if isinstance(error,dict):
                    error=error.get('error',error)
                    if isinstance(error,dict):
                        code=error.get('code') or error.get('type')
                        if isinstance(code,str) and re.fullmatch(r'[a-zA-Z0-9_\-]{1,100}',code):row['error_code']=code
                if row.get('error_code') in ('insufficient_quota','billing_hard_limit_reached','credit_balance_exhausted'):
                    row['status']='provider_quota_exhausted'
            # Reprice all responses with the single final price file, including failed
            # validations that still consumed tokens. Legacy pilot helpers stay intact.
            raw=row.get('provider_response')
            if raw is not None:
                try:
                    if c['provider']=='openai' and raw.get('service_tier') not in (None,'default'):
                        raise pricing.PricingError('Unexpected non-standard service tier')
                    usage=pricing.normalize_usage(c['provider'],raw)
                    details=pricing.cost_details(c['model'],usage,self.pricing)
                    row.update(usage=usage,cost_usd=details['total'],cost_details=details,
                               pricing_sha256=self.plan['pricing_sha256'],pricing_verified_date=self.pricing['verified_date'],
                               actual_service_tier=raw.get('service_tier'))
                except (KeyError,ValueError,TypeError) as exc:
                    row.update(status='pricing_failure',cost_usd=None,cost_details=None,
                               pricing_error_kind=type(exc).__name__)
            row.update(key=key,role=role,created_at=start['created_at'],ended_at=rt.utc(),metadata=metadata,
                       task_id=metadata.get('task_id'),batch_id=metadata.get('batch_id'),cohort=metadata.get('cohort'),
                       freeze_sha256=self.freeze,latency_ms=round((time.perf_counter()-began)*1000),
                       budget_charge_usd=row['cost_usd'] if row['cost_usd'] is not None else reserved,
                       unknown_cost_reservation_usd=reserved if row['cost_usd'] is None else 0)
            # Durable local result precedes telemetry; an exporter failure cannot repeat a paid call.
            with self.lock:
                put(W/'results'/f'{key}.json',row);self.records.append(row)
                self.charge+=row['budget_charge_usd']-reserved;self.inflight-=1
            observation.finish(row)
        print(json.dumps(dict(key=key,status=row['status'],budget_ledger_usd=round(self.charge,6))),flush=True)
        return row

    def call(self,logical,role,payload,parents=()):
        previous=sorted((W/'started').glob(logical+'__a*.json'))
        for path in previous:
            start=read(path);row=read(W/'results'/path.name)
            if start['payload']!=payload or set(start['parent_sha256'])!=set(parents):raise RuntimeError('Resume input changed: '+logical)
            if any(digest(W/'results'/f'{parent}.json')!=h for parent,h in start['parent_sha256'].items()):
                raise RuntimeError('Resume parent content changed: '+logical)
            if row['status']=='success':return row['output'],row['key']
        technical=transport=limited=0
        # Per-resume limits prevent an error storm. Global calls/budget remain fixed across resumes.
        for attempt in range(len(previous)+1,len(previous)+self.plan['rate_limit_retry_limit']+1):
            row=self.once(f'{logical}__a{attempt:03}',role,payload,parents)
            if row['status']=='success':return row['output'],row['key']
            # Preserve and retry transient/request-level provider failures under the
            # frozen transport retry budget; authentication, model, quota, pricing,
            # and not-found failures remain immediate stops.
            if row['status'] in ('model_mismatch','provider_quota_exhausted','pricing_failure') or row.get('http_status') in (401,403,404):
                self.abort.set();raise rt.StopRun(row['status']+': '+logical)
            if row.get('http_status')==429:
                limited+=1
                provider='google' if role=='evaluator' else self.plan['templates'][role]['candidate']['provider']
                with self.pacing:self.next_request[provider]=time.monotonic()+min(60*2**min(limited-1,2),240)
            elif row['status']=='transport_failure':transport+=1
            else:technical+=1
            if technical>=self.plan['schema_retry_limit'] or transport>=self.plan['transport_retry_limit']:break
            self.abort.wait(min(2**min(attempt,4),16))
        self.abort.set();raise rt.StopRun('retry_exhausted_pause_for_recovery: '+logical)

    def close_batch(self,batch,records,register,history):
        metadata=dict(task_id=None,batch_id=batch,cohort='natural',condition='curator')
        class BatchState(TypedDict):
            result: dict
        graph=StateGraph(BatchState)
        graph.add_node('lesson_curator',lambda _:dict(result=super(Runner,self).close_batch(batch,records,register,history)))
        graph.add_edge(START,'lesson_curator');graph.add_edge('lesson_curator',END)
        token=self.context.set(metadata)
        try:
            with self.telemetry.task(f'batch{batch}_curator',metadata):
                return graph.compile(name='Study E batch memory').invoke({})['result']
        finally:self.context.reset(token)


def prepare_mixed(plan):
    path=W/'mixed_inputs.json'
    if path.exists():
        stored=read(path)
        if stored['plan_sha256']!=digest(W/'execution_plan.json') or stored['transformation_sha256']!=digest(HERE/'defects.py'):
            raise RuntimeError('Mixed input transformation/plan changed')
        for entry in stored['items']:
            if entry['source_sha256']!=digest(W/'tasks'/f"{entry['source_task_id']}.json"):
                raise RuntimeError('Mixed original changed: '+entry['source_task_id'])
        expected=stored['content_sha256']
        if expected!=sha(stored['items']):raise RuntimeError('Mixed input contents changed')
        return stored['items']
    entries=[]
    for index,source_id in enumerate(plan['mixed_order'],1):
        sourcepath=W/'tasks'/f'{source_id}.json';source=read(sourcepath)
        t=next(t for t in plan['tasks'] if t['task_id']==source_id)
        assignment=plan['mixed_assignment'].get(source_id)
        change=mutate(source['initial'],assignment['defect_type'],assignment['variant'],source['topic']) if assignment else None
        entries.append(dict(task_id=f'SE-FINAL-M{index:03}',index=index,batch_id=(index-1)//31+1 if index<=93 else 4,
                            source_task_id=source_id,source_sha256=digest(sourcepath),
                            initial=change['modified'] if change else source['initial'],
                            condition=assignment['defect_type'] if assignment else 'unchanged',change=change,
                            source_batch_id=t['batch_id']))
    put(path,dict(created_at=rt.utc(),plan_sha256=digest(W/'execution_plan.json'),
                  transformation_sha256=digest(HERE/'defects.py'),content_sha256=sha(entries),items=entries))
    return entries


def source_files():
    files=list(HERE.glob('*.py'))+[HERE/'requirements.lock.txt',S/'215_FINAL_EXPERIMENT_PROTOCOL_DRAFT.md',
                                 W/'execution_plan.json',W/'selected_topics.json',W/'topic_inventory.json',ROOT/'주제.md',
                                 S.parent/'study_d/config/persona_experiment.md',S.parent/'study_d/config/company_evidence.md',
                                 S/'tools/pilot125_v1/run.py',S/'tools/long125_v2/run.py',S/'tools/planning_research_v2/finalize_reference.py']
    files += [S/rel for rel in rt.source_snapshot()]
    files += [pricing.PATH]
    files += [f for f in (W/'pricing').rglob('*') if f.is_file()]
    return sorted(set(files))


def archive_source(path):
    h=digest(path);dest=W/'source_archive'/h
    if dest.exists():
        if digest(dest)!=h:raise RuntimeError('Source archive changed')
    else:
        dest.parent.mkdir(parents=True,exist_ok=True)
        with dest.open('xb') as out:out.write(path.read_bytes())
    return h


def freeze():
    plan=prepare()
    receipt=read(W/'offline_test_receipt.json')
    if not receipt['passed'] or receipt['plan_sha256']!=digest(W/'execution_plan.json'):raise RuntimeError('Fresh offline check required')
    hashes={f.relative_to(ROOT).as_posix():digest(f) for f in source_files()}
    if receipt.get('source_sha256')!=hashes:raise RuntimeError('Source changed after offline check')
    for f in source_files():archive_source(f)
    put(W/'freeze.json',dict(status='local_freeze_not_registration',created_at=rt.utc(),source_sha256=hashes,
                            offline_test_sha256=digest(W/'offline_test_receipt.json')))
    return read(W/'freeze.json')


def verify_live():
    frozen=read(W/'freeze.json');registration=read(W/'registration.json')
    if registration['freeze_sha256']!=digest(W/'freeze.json'):raise RuntimeError('Registration/freeze mismatch')
    expected=dict(frozen['source_sha256'])
    allowed={str((HERE/f).relative_to(ROOT).as_posix()) for f in ('run.py','telemetry.py')}
    for patchpath in sorted((W/'patches').glob('*.json')):
        patch=read(patchpath)
        if patch['freeze_sha256']!=digest(W/'freeze.json') or not patch['scientific_inputs_unchanged']:
            raise RuntimeError('Invalid recovery receipt')
        for rel,change in patch['changes'].items():
            if rel not in allowed or expected[rel]!=change['old_sha256']:raise RuntimeError('Invalid recovery chain')
            expected[rel]=change['new_sha256']
    for rel,h in expected.items():
        if digest(ROOT/rel)!=h:raise RuntimeError('Frozen source changed; document recovery/re-freeze as applicable: '+rel)
    plan=read(W/'execution_plan.json')
    import importlib.metadata
    if any(importlib.metadata.version(k)!=v for k,v in plan['installed_versions'].items()):raise RuntimeError('SDK changed')
    return plan


def record_recovery(kind,reason):
    """Record equivalent operational fixes; never silently rewrite scientific inputs.

    Exact diffs require human/agent review. The allowlist is an engineering guard,
    not an automatic proof that arbitrary code changes preserve semantics.
    """
    frozen=read(W/'freeze.json');expected=dict(frozen['source_sha256'])
    if read(W/'registration.json')['freeze_sha256']!=digest(W/'freeze.json'):raise RuntimeError('Registration mismatch')
    for path in sorted((W/'patches').glob('*.json')):
        for rel,c in read(path)['changes'].items():
            if expected[rel]!=c['old_sha256']:raise RuntimeError('Broken recovery chain')
            expected[rel]=c['new_sha256']
    allowed={(HERE/f).relative_to(ROOT).as_posix() for f in ('run.py','telemetry.py')}
    changes={rel:dict(old_sha256=h,new_sha256=digest(ROOT/rel)) for rel,h in expected.items() if digest(ROOT/rel)!=h}
    if not changes or not set(changes)<=allowed:raise RuntimeError('Only equivalent run/telemetry recovery changes allowed; scientific changes need a new protocol/version')
    tests=read(W/'offline_test_receipt.json')
    if not tests['passed'] or tests.get('source_sha256')!={f.relative_to(ROOT).as_posix():digest(f) for f in source_files()}:raise RuntimeError('Run current offline checks before recovery')
    for rel,change in changes.items():
        old=W/'source_archive'/change['old_sha256']
        if digest(old)!=change['old_sha256']:raise RuntimeError('Original source archive changed')
        archive_source(ROOT/rel)
        change['unified_diff']=''.join(difflib.unified_diff(old.read_text(encoding='utf-8').splitlines(True),
            (ROOT/rel).read_text(encoding='utf-8').splitlines(True),fromfile=rel+'@before',tofile=rel+'@after'))
    put(W/'patches'/f'{time.time_ns()}.json',dict(created_at=rt.utc(),kind=kind,reason=reason,
        freeze_sha256=digest(W/'freeze.json'),changes=changes,scientific_inputs_unchanged=True,
        scientific_equivalence='Declared operational correction; exact code changes must be reviewed against frozen roles/routing/inputs/criteria.',
        tests_sha256=digest(W/'offline_test_receipt.json')))


def execute(which):
    plan=verify_live()
    pricing.validate_plan(plan,pricing.load_pricing())
    pricing.validate_date(pricing.load_pricing())
    from dotenv import load_dotenv
    load_dotenv(ROOT/'.env',override=False)
    telemetry=Telemetry('study-e-final125-v1',enabled=True,
                        failure_sink=lambda value:put(W/'telemetry_events'/f'{time.time_ns()}.json',value))
    if not telemetry.healthcheck()['ready_for_paid_calls']:
        raise RuntimeError('Live Langfuse authentication required before paid calls')
    lockpath=S/'private/role_selection_budget.lock'
    lockpath.parent.mkdir(parents=True,exist_ok=True)
    lock=lockpath.open('x',encoding='utf-8');lock.write('final125_v1');lock.flush()
    clients={};runner=None;reason=None
    try:
        clients=rt.api.create_clients(plan)
        from google import genai
        from google.genai import types
        clients['google']=genai.Client(api_key=os.environ['GOOGLE_API_KEY'],http_options=types.HttpOptions(timeout=180000,retry_options=types.HttpRetryOptions(attempts=1)))
        runner=Runner(plan,clients,telemetry)
        if which in ('natural','both'):
            register=[];history=[];parent=None
            for batch in range(1,5):
                tasks=[t for t in plan['tasks'] if t['batch_id']==batch]
                with ThreadPoolExecutor(max_workers=plan['workers']) as pool:
                    records=list(pool.map(lambda t:runner.task(t,copy.deepcopy(register),parent),tasks))
                closed=runner.close_batch(batch,sorted(records,key=lambda r:r['task_id']),register,history)
                register,history,parent=closed['register'],closed['history'],closed['memory_parent']
        if which in ('mixed','both'):
            entries=prepare_mixed(plan)
            with ThreadPoolExecutor(max_workers=plan['workers']) as pool:
                list(pool.map(runner.task,entries))
    except Exception as exc:
        if runner:runner.abort.set()
        reason=type(exc).__name__+': '+(telemetry.sanitize(str(exc)) if isinstance(exc,(rt.StopRun,RuntimeError,AssertionError)) else 'See local attempt record')
    finally:
        try:
            put(W/'telemetry_sessions'/f'{time.time_ns()}.json',telemetry.flush())
            if runner:
                rows=runner.records
                put(W/'sessions'/f'{time.time_ns()}.json',dict(at=rt.utc(),requested=which,stop_reason=reason,
                    completed_natural=len(list((W/'tasks').glob('SE-FINAL-N*.json'))),completed_mixed=len(list((W/'tasks').glob('SE-FINAL-M*.json'))),
                    attempts=len(rows),known_cost_usd=sum(r['cost_usd'] for r in rows if r.get('cost_usd') is not None),
                    unknown_reservation_usd=sum(r['budget_charge_usd'] for r in rows if r.get('cost_usd') is None),
                    budget_ledger_usd=runner.charge,actual_billed_cost_not_claimed=True))
        finally:
            for client in clients.values():
                try:client.close()
                except Exception:pass
            lock.close();lockpath.unlink()
    if reason:raise RuntimeError(reason)


def main():
    parser=argparse.ArgumentParser()
    sub=parser.add_subparsers(dest='command',required=True)
    sub.add_parser('prepare');sub.add_parser('freeze')
    reg=sub.add_parser('record-registration');reg.add_argument('--id',required=True);reg.add_argument('--url',required=True)
    recovery=sub.add_parser('record-recovery');recovery.add_argument('--kind',choices=['transport','serialization','checkpoint_recovery','telemetry'],required=True);recovery.add_argument('--reason',required=True)
    run=sub.add_parser('execute');run.add_argument('--condition',choices=['natural','mixed','both'],default='both')
    args=parser.parse_args()
    if args.command=='prepare':prepare()
    elif args.command=='freeze':freeze()
    elif args.command=='record-registration':
        if not re.fullmatch(r'\d+',args.id) or not args.url.startswith('https://aspredicted.org/'):raise ValueError('Actual AsPredicted ID and URL required')
        if list((W/'started').glob('*.json')):raise RuntimeError('Cannot retrospectively register an executed workload')
        put(W/'registration.json',dict(id=args.id,url=args.url,recorded_at=rt.utc(),freeze_sha256=digest(W/'freeze.json'),
                                     provenance='Operator-supplied actual registration; entry alone does not prove server publication.'))
    elif args.command=='record-recovery':record_recovery(args.kind,args.reason)
    else:execute(args.condition)


if __name__=='__main__':main()
