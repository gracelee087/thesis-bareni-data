"""Typed ID domains and deterministic proposal checks; meaning needs human audit."""
import json
from jsonschema import Draft202012Validator

def need(test,msg):
    if not test:raise ValueError(msg)
def obj(p):return dict(type='object',additionalProperties=False,properties=p,required=list(p))
def arr(v):return dict(type='array',items=v)
def text():return dict(type='string')
def enum(v):return dict(type='string',enum=v)
def nullable_enum(v):return dict(type=['string','null'],enum=v+[None])
def source_ids(p):return [s['source_id'] for s in p['company_evidence']+p.get('task_evidence',[])]
def length_check(p):
    n=len(p['draft']['body']); lower=p['body_length_bounds']['min'];upper=p['body_length_bounds']['max']
    return dict(characters=n,min=lower,max=upper,failed=not lower<=n<=upper)
def target_ids(p):return [d['defect_id'] for d in p['gate_assessment']['defects']]+(['LENGTH'] if length_check(p)['failed'] else [])
def validate_input(p):
    role=p['role'];need(role in ('critic','memory'),'unknown role')
    need(p['item_id'].startswith('E-CRIT-' if role=='critic' else 'E-MEM-'),'item prefix')
    if role=='critic':
        need(len(source_ids(p))==len(set(source_ids(p))),'duplicate sources')
        ids=[d['defect_id'] for d in p['gate_assessment']['defects']]
        need(len(ids)==len(set(ids)),'duplicate defects')
        for d in p['gate_assessment']['defects']:
            need(d['severity'] in ('critical','noncritical'),'severity')
            need(set(d['source_ids'])<=set(source_ids(p)),'unknown defect source')
            need(d['quote'] is None or d['quote'] in p['draft']['body'],'defect quote mismatch')
        need(p['mechanical_check']==length_check(p),'length mismatch')
    else:
        need(1<=p['max_proposals']<=3,'proposal cap')
        need(1<=p['max_register_entries']<=12,'register cap')
        need(len(p['lesson_register'])<=p['max_register_entries'],'overfull input register')
        events=p['history_events']+p['batch_events'];ids=[e['event_id'] for e in events]
        need(len(ids)==len(set(ids)),'duplicate event IDs')
        need(all(e['status'] in ('confirmed','unverified') for e in events),'event status')
        lessons=p['lesson_register'];need(len({l['lesson_id'] for l in lessons})==len(lessons),'duplicate lessons')
        need(all(set(l['source_event_ids'])<=set(ids) for l in lessons),'unknown historical provenance')
    return p
def schema(p):
    if p['role']=='critic':
        targets=target_ids(p)
        # With no permitted targets, the only valid result is an empty repairs array.
        target_schema=enum(targets) if targets else dict(type='string')
        repairs=arr(obj(dict(repair_id=enum(['P01','P02','P03','P04']),target_ids=arr(target_schema),instruction=text(),source_ids=arr(enum(source_ids(p))))))
        return obj(dict(item_id=enum([p['item_id']]),repairs=repairs))
    events=[e['event_id'] for e in p['history_events']+p['batch_events']]
    lessons=[l['lesson_id'] for l in p['lesson_register']]
    return obj(dict(item_id=enum([p['item_id']]),proposals=arr(obj(dict(proposal_id=enum(['P01','P02','P03']),action=enum(['ADD','MERGE','SKIP']),target_lesson_id=nullable_enum(lessons),event_ids=arr(enum(events)),lesson_text=dict(type=['string','null']),reason=text())))))
def validate_output(v,p):
    Draft202012Validator(schema(p)).validate(v)
    if p['role']=='critic':
        rows=v['repairs'];need(len(rows)<=4,'too many repairs')
        need([r['repair_id'] for r in rows]==[f'P{i:02}' for i in range(1,len(rows)+1)],'ordered repair IDs')
        for r in rows:
            need(r['instruction'].strip(),'empty instruction')
            need(r['target_ids'] and set(r['target_ids'])<=set(target_ids(p)),'invalid repair target')
            need(len(r['target_ids'])==len(set(r['target_ids'])),'duplicate target ID')
        return v
    rows=v['proposals'];need(1<=len(rows)<=p['max_proposals'],'proposal count')
    need([r['proposal_id'] for r in rows]==[f'P{i:02}' for i in range(1,len(rows)+1)],'ordered proposal IDs')
    existing={l['lesson_id']:l for l in p['lesson_register']};updated=set();adds=0
    for r in rows:
        need(r['reason'].strip() and r['event_ids'],'missing reason/provenance')
        need(len(r['event_ids'])==len(set(r['event_ids'])),'duplicate provenance')
        a=r['action'];target=r['target_lesson_id']
        if a=='SKIP':need(r['lesson_text'] is None,'SKIP text must be null')
        else:
            need(type(r['lesson_text']) is str and r['lesson_text'].strip(),'empty lesson')
            if a=='ADD':need(target is None,'ADD target must be null');adds+=1
            else:
                need(target in existing and target not in updated,'MERGE target')
                need(set(existing[target]['source_event_ids'])<=set(r['event_ids']),'lost MERGE provenance')
                updated.add(target)
    need(len(existing)+adds<=p['max_register_entries'],'projected capacity exceeded')
    return v
def parse(raw,p):
    def unique(pairs):
        d={}
        for k,v in pairs:need(k not in d,'duplicate JSON key');d[k]=v
        return d
    value=json.loads(raw,object_pairs_hook=unique,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('nonfinite JSON')))
    return validate_output(value,p)
