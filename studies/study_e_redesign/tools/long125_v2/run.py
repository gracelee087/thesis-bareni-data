"""Length-only adaptation of the completed pilot; immutable old run preserved."""
import copy, importlib.util, json, re, sys
from pathlib import Path
from pydantic import Field

S=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('long125_base',S/'tools/pilot125_v1/run.py')
p=importlib.util.module_from_spec(spec);sys.modules[spec.name]=p;spec.loader.exec_module(p)
rt=p.rt;W=S/'private/long125_v2';p.W=W;rt.W=W
read,save,digest,sha=p.read,p.save,p.digest,p.sha

class LongGateInput(rt.gate.GateInput):
    body: str=Field(min_length=150,max_length=2000)

rt.gate.GateInput=LongGateInput
rt.api.GateInput=LongGateInput

def validate_post(value,iid):
    need=rt.post.require
    need(type(value) is dict and set(value)=={'item_id','title','body'},'output fields mismatch')
    need(all(type(x) is str for x in value.values()),'output values must be strings')
    need(value['item_id']==iid,'wrong item ID')
    need(1<=len(value['title'])<=80 and value['title'].strip(),'invalid title')
    need(150<=len(value['body'])<=2000 and value['body'].strip(),'body outside 150-2000 characters')
    return value

rt.post.validate_output=validate_post
old_critic=rt.critic_input

def critic_input(*args,**kwargs):
    value=old_critic(*args,**kwargs)
    value['body_length_bounds']['max']=2000
    value['mechanical_check']=rt.cm.length_check(value)
    rt.cm.validate_input(value)
    return value

rt.critic_input=critic_input

def lengths(value):
    if isinstance(value,list):return [lengths(x) for x in value]
    if isinstance(value,dict):return {k:lengths(v) for k,v in value.items()}
    if isinstance(value,str):
        value=re.sub(r'300\s*[–-]\s*450','1200-1500',value)
        value=re.sub(r'150\s*[–-]\s*600','150-2000',value)
        value=re.sub(r'150\s+(?:through|to)\s+600', '150 to 2000', value)
    return value

def prepare():
    if (W/'execution_plan.json').exists():return read(W/'execution_plan.json')
    old=read(S/'private/pilot125_v1/execution_plan.json');plan=copy.deepcopy(old)
    plan['templates']=lengths(old['templates'])
    plan['tasks']=lengths(old['tasks'])
    plan['templates']['researcher']['request']['max_tokens']=4096
    plan['technical_change']='Researcher output ceiling2048 to4096 after seven max_tokens failures on one six-claim input in superseded800 run; no model replacement.'
    for role in ['writer','optimizer']:
        plan['templates'][role]['system']+='\n\nAim for a substantive body of1200-1500 characters, never exceeding2000 characters. Use the available space to explain the bounded decision and its qualifications clearly, without padding or unsupported facts.'
    for t,previous in zip(plan['tasks'],old['tasks']):
        t['paired_short_task_id']=previous['task_id'];t['task_id']=previous['task_id'].replace('SE-PILOT-','SE-LONG2-')
    plan.update(created_at=rt.utc(),authorization='User: run125 paid with latest target1200-1500/max2000; retain cumulative below USD50. Prior proposed stage$5 limit belonged to cancelled20 plan and does not apply to authorized125.',prior_budget_charge_usd=read(S/'private/long125_v1/supersession_receipt.json')['cumulative_budget_charge_usd'],cap_usd=49.99,length=dict(target_min=1200,target_max=1500,min=150,max=2000,title_excluded=True,spaces_newlines_included=True),paired_short_plan_sha256=digest(S/'private/pilot125_v1/execution_plan.json'),policy='Exploratory longer-body rerun of the same125 frozen topics/CF-PF assignments in the same order, avoiding topic selection confounding. Fresh outputs; no short outputs or scores supplied. Same models/settings/rubric and 31/31/31/32 batches. Both runs start with empty memory; this run accumulates its own lessons. Length is the intended intervention, but random generation, time and endogenous memory differences prevent interpreting the comparison as a clean randomized causal effect. Original125 unchanged; these are125 matched topics, not250 unique tasks. H1 uses150-2000. Target1200-1500 is a target, not a post-hoc pass filter. No quality-based retries. Cumulative cap49.99, conservative cancellation reserves retained.')
    # Preserve old source entries but freeze current bytes used by this run.
    for rel in plan['source_sha256']:plan['source_sha256'][rel]=digest(S.parents[1]/rel)
    for path in [Path(__file__),S/'194_LONGER_CONTENT_CONDITION.md',S/'198_LONG125_V2_EXECUTION_PLAN.md',S/'private/long125_v1/supersession_receipt.json']:
        plan['source_sha256'][str(path.relative_to(S.parents[1]))]=digest(path)
    plan['role_source_sha256']=rt.source_snapshot()
    plan['sdk_versions']=rt.api.versions()
    save(W/'execution_plan.json',plan)
    print(json.dumps(dict(prepared=125,prior=plan['prior_budget_charge_usd'],remaining=plan['cap_usd']-plan['prior_budget_charge_usd'],models={r:t['candidate']['model'] for r,t in plan['templates'].items()})),flush=True)
    return plan

def check():
    plan=read(W/'execution_plan.json');old=read(S/'private/pilot125_v1/execution_plan.json')
    assert len(plan['tasks'])==125 and len({t['task_id'] for t in plan['tasks']})==125
    assert [t['topic'] for t in plan['tasks']]==[t['topic'] for t in old['tasks']]
    assert plan['batch_sizes']==[31,31,31,32]
    assert all(plan['templates'][r]['candidate']==old['templates'][r]['candidate'] for r in plan['templates'])
    for t in plan['tasks']:
        assert 'body target 1200-1500 characters, hard range 150-2000' in t['brief']
        assert not re.search(r'300[–-]450|150(?:[–-]| to | through )600',json.dumps(t,ensure_ascii=False))
        pp=p.planner_input(t,[]);rt.native_schema('planner',pp)
        pl=dict(item_id=pp['item_id'],selected_lessons=[],steps=[dict(step_id=f'P{i:02}',instruction='Suggest checking one copied record manually.',requirement_ids=[f'R{i:02}'],lesson_ids=[],evidence_ids=['S01']) for i in (1,2)],constraints_to_preserve=[])
        rp=p.research_input(t,pl,[]);rt.native_schema('researcher',rp);work=copy.deepcopy(t);work['research']=rp
        wp=p.production(work,'writer',plan=pl,ledger={'ledger':[]});rt.native_schema('writer',wp)
        draft=dict(title='One bounded workflow check',body='A'*1350)
        gp=rt.gate_input(work,draft,f"GATE-BLIND-{t['index']:03}",plan['templates']['gate']['rules'])
        rt.request_for('gate',gp,plan['templates']['gate'])
        cp=rt.critic_input(work,draft,dict(defects=[]),gp,'E-CRIT-check');rt.native_schema('critic',cp)
        assert cp['mechanical_check']['max']==2000 and not cp['mechanical_check']['failed']
        op=p.production(work,'optimizer',draft=draft,repairs={'repairs':[]});rt.native_schema('optimizer',op)
        ep=rt.evaluator_input(work,draft,f"EVAL-BLIND-{t['index']:03}")
        assert 'body target 1200-1500 characters, hard range 150-2000' in ep['request']['contents']
        for role,payload in [('planner',pp),('researcher',rp),('writer',wp),('optimizer',op),('critic',cp)]:
            request=rt.request_for(role,payload,plan['templates'][role])
            assert not re.search(r'300[–-]450|150(?:[–-]| to | through )600',json.dumps(request,ensure_ascii=False))
    for n,valid in [(149,False),(150,True),(600,True),(1200,True),(1500,True),(2000,True),(2001,False)]:
        draft=dict(item_id='E-WRITE-301',title='Boundary',body='A'*n)
        try:rt.post.parse_output(json.dumps(draft),draft['item_id']);accepted=True
        except ValueError:accepted=False
        assert accepted==valid
        gate=copy.deepcopy(gp);gate['body']='A'*n
        try:LongGateInput.model_validate(gate);accepted=True
        except ValueError:accepted=False
        assert accepted==valid
    receipt=dict(passed=True,paid_calls=0,checked_tasks=125,checked_length_boundaries=[149,150,600,1200,1500,2000,2001],models_unchanged=True,all_role_requests_length_updated=True,plan_sha256=digest(W/'execution_plan.json'),adapter_sha256=digest(Path(__file__)))
    p.put(W/'offline_test_receipt.json',receipt);print(json.dumps(receipt),flush=True)

if __name__=='__main__':
    command=sys.argv[1]
    if command=='prepare':prepare()
    elif command=='check':check()
    elif command=='execute':p.run()
