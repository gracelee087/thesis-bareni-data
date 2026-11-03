"""Read-only complete Langfuse reconciliation; no model calls or cloud writes."""
import json, math, sys, hashlib, logging, time
from pathlib import Path
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict
import httpx
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[3]
W = ROOT / 'studies/study_e_redesign/private/final125_v1'
OUT = W / 'reports_final_2026-09-08/cloud_audit'
sys.path.insert(0, str(Path(__file__).parent / 'final125_v1'))
import pricing
from telemetry import Telemetry
logging.disable(logging.CRITICAL)
def read(p): return json.loads(p.read_text('utf-8'))
def save(p,v): p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    env=dotenv_values(ROOT/'.env')
    identity=read(W/'execution_identity_2026-09-08.json')
    rows={p.stem:read(p) for p in (W/'results').glob('*.json')}
    starts={p.stem:read(p) for p in (W/'started').glob('*.json')}
    refs={}
    for p in (W/'telemetry_sessions').glob('*.json'):
        for a in read(p)['attempts']:
            assert a['attempt_key'] not in refs
            refs[a['attempt_key']]=a
    assert set(refs)==set(rows)==set(starts)
    groups=defaultdict(list)
    for k,a in refs.items(): groups[a['trace_id']].append(k)
    sanitizer=Telemetry('audit',enabled=False)
    sanitizer._secrets=tuple(v for k,v in env.items() if v and any(s in k.upper() for s in ('KEY','SECRET','TOKEN','PASSWORD')))
    result={'at':datetime.now(timezone.utc).isoformat(),'execution_identity_sha256':digest(W/'execution_identity_2026-09-08.json'),'read_only':True,'model_calls':0,'expected_attempts':len(rows),'expected_traces':len(groups),'checks':[],'errors':[]}
    with httpx.Client(base_url=(env.get('LANGFUSE_HOST') or env['LANGFUSE_BASE_URL']).rstrip('/'),auth=(env['LANGFUSE_PUBLIC_KEY'],env['LANGFUSE_SECRET_KEY']),timeout=45) as client:
        response=client.get('/api/public/projects');response.raise_for_status()
        projects=response.json()['data']
        assert len(projects)==1 and projects[0]['id']==identity['langfuse_project_id'], 'Wrong project'
        result['project_id']=projects[0]['id'];result['project_name']=projects[0]['name']
        # Read paginated generations once, avoiding hundreds of per-trace requests.
        bulk={}
        for page in range(1,100):
            cache=OUT/f'observations_page_{page:03}.json'
            if cache.exists(): data=read(cache)
            else:
                for retry in range(6):
                    response=client.get('/api/public/observations',params={'page':page,'limit':100,'type':'GENERATION'})
                    if response.status_code!=429: break
                    print('Read-only Langfuse rate limit; waiting before retry',flush=True)
                    time.sleep(min(float(response.headers.get('retry-after','30')),60))
                response.raise_for_status();data=sanitizer.sanitize(response.json());save(cache,data)
                time.sleep(2)
            for o in data['data']: bulk.setdefault(o['traceId'],[]).append(o)
            print(json.dumps({'cloud_page':page,'generations_read':sum(len(v) for v in bulk.values())}),flush=True)
            if page>=data['meta']['totalPages']:break
        result['project_generation_count']=sum(len(v) for v in bulk.values())
        def fetch(trace_id):
            path=OUT/(trace_id+'.json')
            if path.exists(): return trace_id,read(path)
            trace={'id':trace_id,'observations':bulk.get(trace_id,[]),'source':'paginated_public_observations'}
            save(path,trace)
            return trace_id,trace
        with ThreadPoolExecutor(max_workers=4) as pool:
            futures={pool.submit(fetch,t):t for t in groups}
            for future in as_completed(futures):
                tid=futures[future]
                try:
                    tid,trace=future.result()
                    obs={o['id']:o for o in trace.get('observations',[])}
                    expected_ids={refs[k]['observation_id'] for k in groups[tid]}
                    actual_ids={o['id'] for o in obs.values() if o.get('type')=='GENERATION'}
                    if actual_ids!=expected_ids: result['errors'].append({'trace_id':tid,'kind':'generation_set_mismatch','missing':sorted(expected_ids-actual_ids),'extra':sorted(actual_ids-expected_ids)})
                    for k in groups[tid]:
                        a=refs[k];r=rows[k];s=starts[k];o=obs.get(a['observation_id'])
                        if o is None:
                            result['errors'].append({'key':k,'kind':'missing_observation'});continue
                        expected_output=r.get('output')
                        if expected_output is None and r.get('raw_text') is not None: expected_output={'unparsed_model_output':r['raw_text']}
                        checks={
                            'status':o.get('statusMessage')==r['status'],
                            'level':o.get('level')==('DEFAULT' if r['status']=='success' else 'ERROR'),
                            'model':o.get('model')==s['candidate']['model'],
                            'usage':o.get('usageDetails')==pricing.usage_details(r['usage']),
                            'cost':all(isinstance(o.get('costDetails',{}).get(n),(int,float)) and math.isclose(o['costDetails'][n],v,abs_tol=1e-9,rel_tol=1e-10) for n,v in r['cost_details'].items()),
                            'input':o.get('input')==sanitizer.sanitize({'payload':s['payload'],'request':s['request']}),
                            'output':o.get('output')==sanitizer.sanitize(expected_output),
                            'metadata':o.get('metadata',{}).get('attempt_key')==k and o.get('metadata',{}).get('cost_status')=='known_usage_cost',
                        }
                        result['checks'].append({'key':k,'trace_id':tid,'observation_id':a['observation_id'],'checks':checks,'cloud_cost_usd':o.get('costDetails',{}).get('total')})
                        if not all(checks.values()):result['errors'].append({'key':k,'kind':'field_mismatch','fields':[n for n,v in checks.items() if not v]})
                except Exception as exc:result['errors'].append({'trace_id':tid,'kind':type(exc).__name__,'http_status':getattr(getattr(exc,'response',None),'status_code',None)})
                if len(result['checks'])%100<12: print(json.dumps({'verified_attempts':len(result['checks']),'issues':len(result['errors'])}),flush=True)
    result['verified_attempts']=sum(all(x['checks'].values()) for x in result['checks'])
    result['local_cost_usd']=sum(r['cost_usd'] for r in rows.values())
    result['cloud_cost_usd']=sum(x['cloud_cost_usd'] or 0 for x in result['checks'])
    result['passed']=not result['errors'] and result['verified_attempts']==len(rows)
    result['evidence_sha256']={p.name:digest(p) for p in OUT.glob('*.json') if p.name!='receipt.json'}
    save(OUT/'receipt.json',result)
    print(json.dumps({k:result[k] for k in ('passed','verified_attempts','expected_attempts','expected_traces','local_cost_usd','cloud_cost_usd','errors')}),flush=True)
    return 0 if result['passed'] else 1

if __name__=='__main__': raise SystemExit(main())
