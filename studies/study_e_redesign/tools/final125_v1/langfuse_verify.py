"""Explicitly sync final prices and verify synthetic telemetry; never call LLMs.

Run with --apply after authorizing the new project's pricing setup. Samples are
tagged synthetic in the pricing-verification environment, not experiment data.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
import logging
import math
import os
from pathlib import Path
import time
import httpx
from dotenv import dotenv_values
import pricing
from telemetry import Telemetry

W = pricing.PATH.parent
ROOT = Path(__file__).resolve().parents[4]
RECEIPT = W/'langfuse_pricing_verification_2026-09-07.json'


def save(value):
    RECEIPT.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def tier_fields(row):
    return {k:row[k] for k in ('name','isDefault','priority','conditions','prices')}


def matches(remote, expected):
    return (remote['modelName']==expected['modelName'] and remote['matchPattern']==expected['matchPattern']
            and remote['unit']==expected['unit']
            and sorted([tier_fields(t) for t in remote['pricingTiers']],key=lambda t:t['priority'])==expected['pricingTiers'])


def sync(client,config,receipt):
    expected_project=json.loads((W/'telemetry_reconnect_2026-09-07.json').read_text('utf-8'))['project_id']
    r=client.get('/api/public/projects');r.raise_for_status()
    projects=r.json()['data']
    if len(projects)!=1 or projects[0]['id']!=expected_project:
        raise RuntimeError('Wrong Langfuse project; do not modify')
    receipt['project_id']=expected_project
    all_models=[]
    for page in range(1,100):
        r=client.get('/api/public/models',params={'page':page,'limit':100});r.raise_for_status()
        d=r.json();all_models.extend(d['data'])
        if page>=d['meta']['totalPages']:break
    receipt.setdefault('previous_definitions',[m for m in all_models if m['modelName'] in config['models']])
    receipt.setdefault('models',{})
    for model in config['models']:
        payload=pricing.langfuse_model(model,config)
        candidates=[m for m in all_models if not m['isLangfuseManaged'] and m['modelName']==model]
        exact=next((m for m in candidates if matches(m,payload)),None)
        if candidates and exact is None:
            raise RuntimeError('Existing custom model differs; preserve and review: '+model)
        if exact is None:
            r=client.post('/api/public/models',json=payload);r.raise_for_status();exact=r.json()
        r=client.get('/api/public/models/'+exact['id']);r.raise_for_status();verified=r.json()
        if not matches(verified,payload):
            raise RuntimeError('Remote prices differ: '+model)
        receipt['models'][model]={'id':verified['id'],'payload':payload,'verified':True}
        save(receipt)
        print('Model prices verified: '+model,flush=True)


def smoke(client,config,receipt):
    os.environ['LANGFUSE_TRACING_ENVIRONMENT']='pricing-verification'
    tel=Telemetry('study-e-pricing-verification-20260907')
    tel.healthcheck()
    if not receipt.get('smoke'):
        fixtures=[]
        for role,model in [(r,config['roles'][r]) for r in ('planner','researcher','writer','gate','evaluator')]:
            usage=dict(input_tokens=2000,output_tokens=1000)
            if role=='evaluator':
                usage=dict(prompt_token_count=2000,cached_content_token_count=200,
                    candidates_token_count=400,thoughts_token_count=600,total_token_count=3000)
            if role=='writer':
                usage.update(cached_input_tokens=200,reasoning_tokens=100)
            if role=='researcher':
                usage.update(cached_input_tokens=200,cache_write_input_tokens=300,cache_write_1h_input_tokens=100)
            details=pricing.cost_details(model,usage,config)
            fixtures.append((role,dict(status='success',usage=usage,cost_details=details,
                cost_usd=details['total'],output={'synthetic':True,'body':'Price verification fixture; not model-generated.'},
                pricing_sha256=pricing.pricing_hash(),pricing_verified_date=config['verified_date'])))
        details=pricing.cost_details('gpt-5.4-mini',dict(input_tokens=100,output_tokens=10),config)
        fixtures += [('writer',dict(status='validation_failure',usage=dict(input_tokens=100,output_tokens=10),
            cost_details=details,cost_usd=details['total'],error_kind='ValueError',error_code='synthetic_invalid_json',
            validation_detail='Synthetic example: body field missing',http_status=200)),
            ('writer',dict(status='transport_failure',usage=None,cost_usd=None,budget_charge_usd=123,
                          error_kind='ReadTimeout',error_code='synthetic_timeout',http_status=504))]
        receipt['smoke']={'environment':'pricing-verification','synthetic':True,'observations':[],
            'model_api_calls':0,'actual_provider_charge_usd':0,'status':'started'}
        metadata={'synthetic':True,'exclude_from_experiment':True,'purpose':'pricing_and_error_verification'}
        with tel.task('pricing-verification-20260907',metadata) as trace:
            receipt['smoke']['trace_id']=trace['trace_id']
            save(receipt)
            for index,(role,row) in enumerate(fixtures):
                with tel.attempt('synthetic-'+str(index),role,{'synthetic':True},pricing.candidate(role,config),
                                 {'service_tier':'default'},metadata) as handle:
                    handle.finish(row)
                    receipt['smoke']['observations'].append(dict(id=handle.receipt['observation_id'],
                        expected_status=row['status'],expected_usage=pricing.usage_details(row['usage']),
                        expected_cost_details=row.get('cost_details'),expected_level='DEFAULT' if row['status']=='success' else 'ERROR'))
                    save(receipt)
        tel.flush()
        if tel.errors:
            raise RuntimeError('Telemetry export error; inspect local receipt')
        receipt['smoke']['status']='exported';save(receipt)
    if len(receipt['smoke']['observations'])!=7:
        raise RuntimeError('Incomplete synthetic export; preserve before retrying')
    for attempt in range(12):
        r=client.get('/api/public/traces/'+receipt['smoke']['trace_id'])
        if r.status_code==404:
            time.sleep(3);continue
        r.raise_for_status();trace=r.json()
        obs={o['id']:o for o in trace.get('observations',[])}
        if any(item['id'] not in obs for item in receipt['smoke']['observations']):
            time.sleep(3);continue
        receipt['smoke']['readback']=[]
        for item in receipt['smoke']['observations']:
            o=obs[item['id']]
            assert o['level']==item['expected_level'] and o['statusMessage']==item['expected_status']
            assert o['metadata']['synthetic'] is True and o['metadata']['exclude_from_experiment'] is True
            assert o.get('environment')=='pricing-verification'
            if item['expected_cost_details'] is not None:
                assert o.get('usageDetails')==item['expected_usage']
                for key,value in item['expected_cost_details'].items():
                    assert math.isclose(o['costDetails'][key],value,rel_tol=0,abs_tol=1e-10)
            else:
                assert o['metadata']['cost_status']=='unknown'
                assert not o.get('usageDetails') and not o.get('costDetails')
                assert '123' not in json.dumps(o.get('costDetails'))
            if item['expected_status']=='validation_failure':
                assert o['metadata']['error_code']=='synthetic_invalid_json'
                assert o['metadata']['validation_detail']=='Synthetic example: body field missing'
            receipt['smoke']['readback'].append({k:o.get(k) for k in ('id','name','model','level','statusMessage','usageDetails','costDetails','environment')})
        receipt['smoke'].update(status='verified',verified_at=datetime.now(timezone.utc).isoformat(),
            trace_url=os.environ['LANGFUSE_BASE_URL']+'/project/'+receipt['project_id']+'/traces/'+receipt['smoke']['trace_id'])
        save(receipt);tel.client.shutdown();return
    raise RuntimeError('Synthetic trace readback not complete')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    if not args.apply:
        parser.error('--apply required for authorized cloud model settings and synthetic verification')
    logging.disable(logging.CRITICAL)
    values=dotenv_values(ROOT/'.env')
    for key,value in values.items():
        if key.startswith('LANGFUSE_') and value is not None:os.environ[key]=value
    config=pricing.load_pricing();pricing.validate_date(config)
    receipt=json.loads(RECEIPT.read_text('utf-8')) if RECEIPT.exists() else dict(
        started_at=datetime.now(timezone.utc).isoformat(),pricing_sha256=pricing.pricing_hash(),
        paid_model_calls=0,actual_provider_charge_usd=0)
    if receipt['pricing_sha256']!=pricing.pricing_hash():
        raise RuntimeError('Price file changed after cloud verification started')
    try:
        with httpx.Client(base_url=values['LANGFUSE_BASE_URL'],
            auth=(values['LANGFUSE_PUBLIC_KEY'],values['LANGFUSE_SECRET_KEY']),timeout=30) as client:
            sync(client,config,receipt);smoke(client,config,receipt)
        receipt['completed_at']=datetime.now(timezone.utc).isoformat();receipt['verified']=True
        receipt.pop('last_error_kind',None);save(receipt)
        print(json.dumps({'verified':True,'models':len(receipt['models']),'synthetic_generations':7,
            'paid_model_calls':0,'trace_url':receipt['smoke']['trace_url']}))
    except Exception as exc:
        receipt['last_error_kind']=type(exc).__name__;save(receipt)
        print('Verification failed: '+type(exc).__name__)
        raise SystemExit(1)


if __name__=='__main__':main()
