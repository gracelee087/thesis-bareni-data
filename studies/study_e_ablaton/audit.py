"""Read-only cloud/local reconciliation; reporting only, no provider generation."""
import argparse
from collections import Counter,defaultdict
from datetime import datetime,timezone
import hashlib
import json
import math
from pathlib import Path
import sys
import time
import httpx
from dotenv import dotenv_values

BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[1];W=BASE/'private'
sys.path.insert(0,str(BASE/'tools'))
import pricing
from telemetry import Telemetry

def read(p):return json.loads(p.read_text(encoding='utf-8'))
def save(p,value):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')

def audit(sample=False):
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    dest=W/'cloud_audit'/stamp;dest.mkdir(parents=True)
    env=dotenv_values(ROOT/'.env');sanitizer=Telemetry('audit',enabled=False)
    sanitizer._secrets=tuple(v for k,v in env.items() if v and any(x in k.upper() for x in ['KEY','SECRET','TOKEN','PASSWORD']))
    starts={p.name:read(p) for p in (W/'ledger/started').glob('*.json')}
    results={p.name:read(p) for p in (W/'ledger/results').glob('*.json')}
    refs={p.name:read(p) for p in (W/'telemetry').glob('*.json')}
    keys=sorted(set(starts)&set(results)&set(refs))[:4] if sample else sorted(starts)
    report=dict(study_id='STUDY-E-ABLATON',sample_only=sample,at=stamp,expected=len(keys),checks=[],errors=[])
    with httpx.Client(base_url=(env.get('LANGFUSE_HOST') or env['LANGFUSE_BASE_URL']).rstrip('/'),
         auth=(env['LANGFUSE_PUBLIC_KEY'],env['LANGFUSE_SECRET_KEY']),timeout=45) as client:
        def fetch(path,params=None):
            for attempt in range(4):
                r=client.get(path,params=params)
                if r.status_code!=429:break
                time.sleep(min(30,float(r.headers.get('retry-after',5))))
            r.raise_for_status();return sanitizer.sanitize(r.json())
        project=fetch('/api/public/projects');save(dest/'project.json',project)
        report['project_ids']=[p['id'] for p in project['data']]
        observations={}
        if sample:
            for key in keys:
                oid=refs[key]['observation_id']
                observations[oid]=fetch('/api/public/observations/'+oid)
                save(dest/(oid+'.json'),observations[oid])
        else:
            for page in range(1,200):
                data=fetch('/api/public/observations',dict(page=page,limit=100,type='GENERATION',fromStartTime=read(W/'FREEZE.json')['at']))
                save(dest/f'page_{page:03}.json',data)
                observations.update({o['id']:o for o in data['data']})
                print('CLOUD_PAGE '+str(page),flush=True)
                if page>=data['meta']['totalPages']:break
                time.sleep(1)
        for key in keys:
            if key not in refs or key not in results:
                report['errors'].append(dict(key=key,reason='missing_local_result_or_receipt'));continue
            r=results[key];s=starts[key]['request'];ref=refs[key];o=observations.get(ref['observation_id'])
            if o is None:
                report['errors'].append(dict(key=key,reason='missing_cloud_observation'));continue
            compiled=s['compiled'];known=r.get('cost_usd') is not None
            # Trace input stores the role payload; compiled validation differs by adapter.
            # Provider request is compared exactly, including all actual user content.
            checks=dict(study_id=o.get('metadata',{}).get('study_id')=='STUDY-E-ABLATON',
                trace_id=o.get('traceId')==ref['trace_id'],model=o.get('model')==compiled['model'],
                status=o.get('statusMessage')==r['status'],
                request=o.get('input',{}).get('request')==sanitizer.sanitize(compiled['request']),
                output=o.get('output')==sanitizer.sanitize(r.get('output')),
                usage=o.get('usageDetails')==pricing.usage_details(r['usage']) if known else True,
                cost=all(math.isclose(o.get('costDetails',{}).get(n,-1),v,abs_tol=1e-9) for n,v in r.get('cost_details',{}).items()) if known else o.get('metadata',{}).get('cost_status')=='unknown')
            report['checks'].append(dict(key=key,checks=checks))
            if not all(checks.values()):report['errors'].append(dict(key=key,fields=[k for k,v in checks.items() if not v]))
        if not sample:
            expected_ids={r['observation_id'] for r in refs.values()}
            actual_ids={o['id'] for o in observations.values() if o.get('metadata',{}).get('study_id')=='STUDY-E-ABLATON'}
            if expected_ids!=actual_ids:report['errors'].append(dict(reason='generation_set_mismatch',missing=sorted(expected_ids-actual_ids),extra=sorted(actual_ids-expected_ids)))
    report['passed']=bool(keys) and not report['errors'] and len(report['checks'])==len(keys)
    save(dest/'receipt.json',report)
    print(json.dumps({k:report[k] for k in ['sample_only','expected','passed','errors']}),flush=True)
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--sample',action='store_true');a=p.parse_args()
    raise SystemExit(0 if audit(a.sample)['passed'] else 1)
