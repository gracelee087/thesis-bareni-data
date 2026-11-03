"""Provider-neutral role contracts. Semantic validity is a separate human judgement."""
import json
import re

def need(condition,message):
    if not condition: raise ValueError(message)
def strings(value): return type(value) is list and all(type(x) is str and x.strip() for x in value)
def validate_input(p):
    need(type(p) is dict,'input object required')
    role=p.get('role'); need(role in ('planner','researcher'),'unknown role')
    shared={'role','item_id','brief','company_evidence','task_evidence'}
    extra={'requirements','constraints','lesson_register'} if role=='planner' else {'claims','constraints'}
    need(set(p)==shared|extra,'input fields')
    need(re.fullmatch(r'E-PLAN-5\d{2}' if role=='planner' else r'E-RES-6\d{2}',p['item_id']) is not None,'input ID')
    sources=p['company_evidence']+p['task_evidence']
    need(sources and len({x['source_id'] for x in sources})==len(sources),'unique sources')
    for s in sources:
        need(set(s)=={'source_id','status','text'} and s['status'] in ('approved','superseded','unverified'),'source fields')
        need(all(type(v) is str and v.strip() for v in s.values()),'source strings')
    for key,idkey in [('constraints','constraint_id')]+([('requirements','requirement_id'),('lesson_register','lesson_id')] if role=='planner' else [('claims','claim_id')]):
        values=p[key]; need(type(values) is list,'input list')
        need(len({x[idkey] for x in values})==len(values),'duplicate '+key)
        for x in values: need(set(x)=={idkey,'text'} and all(type(v) is str and v.strip() for v in x.values()),'invalid '+key)
    need(p['constraints'] and (p['requirements'] if role=='planner' else p['claims']),'missing task content')
    return p
def obj(properties): return dict(type='object',additionalProperties=False,properties=properties,required=list(properties))
def arr(item): return dict(type='array',items=item)
def text(): return dict(type='string')
def enum(values): return dict(type='string',enum=values)
def schema(p):
    root={'item_id':enum([p['item_id']])}
    if p['role']=='planner':
        root.update(selected_lessons=arr(obj(dict(lesson_id=text(),application=text()))),steps=arr(obj(dict(step_id=text(),instruction=text(),requirement_ids=arr(text()),lesson_ids=arr(text()),evidence_ids=arr(text())))),constraints_to_preserve=arr(obj(dict(constraint_id=text(),handling=text()))))
    else:
        root['ledger']=arr(obj(dict(claim_id=text(),category=enum(['SUPPORTED','PROPOSED','QUALIFICATIONS','FORBIDDEN']),evidence=arr(obj(dict(source_id=text(),quote=text()))),rationale=text(),use_guidance=text())))
    return obj(root)
def validate_output(value,p):
    from jsonschema import Draft202012Validator
    Draft202012Validator(schema(p)).validate(value)
    def nonempty(v):
        if isinstance(v,str): need(bool(v.strip()),'empty output string')
        elif isinstance(v,list):
            for x in v: nonempty(x)
        elif isinstance(v,dict):
            for x in v.values(): nonempty(x)
    nonempty(value)
    sources={s['source_id'] for s in p['company_evidence']+p['task_evidence']}
    if p['role']=='planner':
        selected=[x['lesson_id'] for x in value['selected_lessons']]
        need(len(selected)==len(set(selected)) and set(selected)<={x['lesson_id'] for x in p['lesson_register']},'invalid selected lesson ID')
        steps=value['steps']; need(2<=len(steps)<=6,'2–6 plan steps required')
        need([s['step_id'] for s in steps]==[f'P{n:02}' for n in range(1,len(steps)+1)],'ordered distinct step IDs')
        for s in steps:
            for key,allowed in [('requirement_ids',{x['requirement_id'] for x in p['requirements']}),('lesson_ids',set(selected)),('evidence_ids',sources)]:
                need(len(s[key])==len(set(s[key])) and set(s[key])<=allowed,'invalid '+key)
        constraints=[x['constraint_id'] for x in value['constraints_to_preserve']]
        need(len(constraints)==len(set(constraints)) and set(constraints)<={x['constraint_id'] for x in p['constraints']},'invalid constraint ID')
    else:
        rows=value['ledger']; ids=[r['claim_id'] for r in rows]
        need(len(ids)==len(set(ids)) and set(ids)=={x['claim_id'] for x in p['claims']},'one row per claim required')
        for row in rows:
            need(all(e['source_id'] in sources for e in row['evidence']),'unknown source ID')
    return value
def parse(raw,p):
    def unique(pairs):
        d={}
        for k,v in pairs:
            need(k not in d,'duplicate JSON key'); d[k]=v
        return d
    value=json.loads(raw,object_pairs_hook=unique,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('non-finite JSON')))
    return validate_output(value,p)
def observable_checks(output,p):
    """Diagnostics only: complete ID coverage or an exact quote does not prove correctness."""
    if p['role']=='planner':
        covered={i for step in output['steps'] for i in step['requirement_ids']}
        return dict(unlinked_requirement_ids=sorted({r['requirement_id'] for r in p['requirements']}-covered),unlisted_constraint_ids=sorted({c['constraint_id'] for c in p['constraints']}-{c['constraint_id'] for c in output['constraints_to_preserve']}))
    sources={s['source_id']:s for s in p['company_evidence']+p['task_evidence']}
    return dict(nonmatching_quotes=[dict(claim_id=r['claim_id'],source_id=e['source_id'],quote=e['quote']) for r in output['ledger'] for e in r['evidence'] if e['quote'] not in sources[e['source_id']]['text']],nonapproved_support_citations=[dict(claim_id=r['claim_id'],source_id=e['source_id']) for r in output['ledger'] if r['category']=='SUPPORTED' for e in r['evidence'] if sources[e['source_id']]['status']!='approved'])
