"""Additional operational crosschecks and submission tables; no API/model calls."""
import json, csv, math, statistics, hashlib
from collections import Counter, defaultdict
from pathlib import Path
from datetime import datetime, timezone
ROOT=Path(__file__).resolve().parents[3]
W=ROOT/'studies/study_e_redesign/private/final125_v1'
OUT=W/'reports_final_2026-09-08'
def read(p):return json.loads(p.read_text('utf-8'))
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def same(a,b):return math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-9)
def csvwrite(name,rows):
    with (OUT/name).open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
rows={p.stem:read(p) for p in (W/'results').glob('*.json')}
starts={p.stem:read(p) for p in (W/'started').glob('*.json')}
tasks={p.stem:read(p) for p in (W/'tasks').glob('*.json')}
logical={k.split('__a')[0]:r for k,r in rows.items() if r['status']=='success'}
plan=read(W/'execution_plan.json')
counts=Counter()
for key,t in tasks.items():
    assert t['initial_gate']==logical[key+'_gate0']['output']
    for field,ref in [('planner','planner_key'),('researcher','researcher_key'),('final','final_key'),('final_gate','final_gate_key')]:
        assert t[field]==rows[t[ref]]['output'],(key,field)
    assert t['initial_eval']==rows[t['evaluation_keys'][0]]['output']
    assert t['final_eval']==rows[t['evaluation_keys'][1]]['output']
    text_same=all(t['initial'][f]==t['final'][f] for f in ('title','body'))
    assert t['evaluation_reused']==text_same
    assert (t['evaluation_keys'][0]==t['evaluation_keys'][1])==text_same
    for i,c in enumerate(t['cycles'],1):
        assert c['critique']==logical[f'{key}_critic{i}']['output']
        assert c['draft']==logical[f'{key}_optimizer{i}']['output']
        assert c['gate']==logical[f'{key}_gate{i}']['output']
        if i==2:assert t['cycles'][0]['gate']['defects']
    if len(t['cycles'])==1:assert not t['cycles'][0]['gate']['defects']
    assert t['final']==t['cycles'][-1]['draft']
    assert t['operational_route']==('needs_human_review' if t['final_gate']['defects'] else 'release_candidate')
    counts[t['operational_route']]+=1
    if key.startswith('SE-FINAL-N'):assert t['initial']==rows[t['writer_key']]['output']
cv={}
for cohort,prefix in [('natural','SE-FINAL-N'),('mixed','SE-FINAL-M')]:
    costs=[]
    for i in range(1,126):
        t=tasks[f'{prefix}{i:03}']
        amount=sum(r['cost_usd'] for r in rows.values() if r.get('task_id')==t['task_id'] and r['role']!='evaluator')
        if cohort=='natural':
            batch=t['batch_id'];n=sum(x['batch_id']==batch for x in plan['tasks'])
            amount+=sum(r['cost_usd'] for r in rows.values() if r['role']=='memory' and r['batch_id']==batch)/n
        costs.append(amount)
    a=read(OUT/f'{cohort}_analysis.json')
    cv[cohort]=statistics.stdev(costs)/statistics.mean(costs)
    assert same(cv[cohort],a['h2']['cv'])
    assert same(sum(costs),a['h2']['known_usage_cost_usd'])
providers=defaultdict(list)
for k,r in rows.items():providers[starts[k]['candidate']['provider']].append(r)
provider_rows=[{'provider':p,'attempts':len(rs),'known_usage_cost_usd':sum(r['cost_usd'] for r in rs),'failed_attempts':sum(r['status']!='success' for r in rs),'failed_usage_cost_usd':sum(r['cost_usd'] for r in rs if r['status']!='success'),'unknown_usage':sum(r.get('cost_usd') is None for r in rs),'invoice_reconciled':False} for p,rs in sorted(providers.items())]
csvwrite('provider_reconciliation.csv',provider_rows)
csvwrite('attempt_costs_1860.csv',[{'attempt_key':k,'provider':starts[k]['candidate']['provider'],'model':starts[k]['candidate']['model'],'task_id':r.get('task_id'),'role':r['role'],'status':r['status'],'created_at':r['created_at'],'ended_at':r['ended_at'],'provider_response_id':r['provider_response'].get('id',r['provider_response'].get('response_id')),'cost_usd':r['cost_usd'],'invoice_matched':False} for k,r in sorted(rows.items())])
flat=[]
for cohort in ('natural','mixed'):
    a=read(OUT/f'{cohort}_analysis.json')
    for dimension,stages in a['quality_scores'].items():
        for stage,stats in stages.items():
            if isinstance(stats,dict) and 'mean' in stats:flat.append({'cohort':cohort,'dimension':dimension,'stage':stage,**stats})
csvwrite('quality_descriptive.csv',flat)
receipt={'at':datetime.now(timezone.utc).isoformat(),'passed':True,'model_calls':0,'tasks_stage_and_output_links_verified':len(tasks),'exact_text_evaluation_reuse_verified':sum(t['evaluation_reused'] for t in tasks.values()),'natural_and_mixed_H2_independent_CV':cv,'routing':dict(counts),'attempt_dates':dict(Counter(r['created_at'][:10] for r in rows.values())),'provider_totals':provider_rows,'invoice_reconciliation':'pending_provider_evidence','script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
save(OUT/'submission_checks.json',receipt)
print(json.dumps(receipt,ensure_ascii=True))
