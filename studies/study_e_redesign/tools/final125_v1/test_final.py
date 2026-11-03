"""Offline full graph/ledger checks, with all socket connections forbidden."""
import copy
import json
import socket
from pathlib import Path
from types import SimpleNamespace
import pytest
import run as m
from test_telemetry import FakeClient


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def forbidden(*a,**k):raise AssertionError('No network allowed in graph tests')
    monkeypatch.setattr(socket.socket,'connect',forbidden)
    monkeypatch.setattr(socket,'create_connection',forbidden)


@pytest.fixture
def workspace(tmp_path,monkeypatch):
    plan=m.read(m.W/'execution_plan.json')
    monkeypatch.setattr(m,'W',tmp_path)
    monkeypatch.setattr(m.p,'W',tmp_path)
    monkeypatch.setattr(m.rt,'W',tmp_path)
    m.put(tmp_path/'execution_plan.json',plan)
    return plan,tmp_path


class Fake(m.Runner):
    def __init__(self,plan,second=False,low=False):
        client=FakeClient();tel=m.Telemetry('offline-graph',client=client);tel.healthcheck()
        super().__init__(plan,{},tel)
        self.calls=[];self.second=second;self.low=low

    def once(self,key,role,payload,parents):
        meta=self.context.get()
        assert meta and meta['cohort'] in ('natural','mixed')
        request=payload['request'] if role=='evaluator' else m.rt.request_for(role,payload,self.plan['templates'][role])
        serialized=json.dumps(request,ensure_ascii=False)
        assert not any(x in serialized for x in ('source_task_id','defect_type','modified_sha256','SE-FINAL-M','mixed_assignment','evaluation_keys'))
        if role=='planner':
            output=dict(item_id=payload['item_id'],selected_lessons=[],steps=[dict(step_id=f'P{i:02}',instruction='Suggest checking one copied record manually.',requirement_ids=[f'R{i:02}'],lesson_ids=[],evidence_ids=['S01']) for i in (1,2)],constraints_to_preserve=[])
        elif role=='researcher':
            output=dict(item_id=payload['item_id'],ledger=[dict(claim_id=x['claim_id'],category='PROPOSED',evidence=[],rationale='Offline fixture: proposed check.',use_guidance='Keep a proposal.') for x in payload['claims']])
        elif role=='writer':
            output=dict(item_id=payload['item_id'],title='One bounded workflow',body=('Choose one copied record and compare its reference with the approved source. '*18)[:1350])
        elif role=='gate':
            pending=self.second and ('_gate0' in key or '_gate1' in key or self.low)
            rule=next(r for r in payload['rules'] if r['severity']=='noncritical' and r['dimension']=='clarity')
            output=dict(schema_version='study-e-gate-v4',item_id=payload['item_id'],assessment_status='assessed',input_problem_reason=None,
                defects=[dict(severity='noncritical',dimension='clarity',location_kind='quote',text_field='body',quote=payload['body'][:20],missing_requirement=None,rule_id=rule['rule_id'],evidence_ids=['BRIEF'],reason='Offline fixture')] if pending else [])
            m.rt.gate.validate_output(output,m.rt.gate.GateInput.model_validate(payload))
        elif role=='critic':
            targets=m.rt.cm.target_ids(payload)
            output=dict(item_id=payload['item_id'],repairs=[dict(repair_id='P01',target_ids=targets,instruction='Preserve the approved scope.',source_ids=['BRIEF'])] if targets else [])
        elif role=='optimizer':
            output=dict(item_id=payload['item_id'],**payload['draft'])
            if self.second:output['body']+=' '
        elif role=='memory':output=dict(item_id=payload['item_id'],proposals=[dict(proposal_id='P01',action='SKIP',target_lesson_id=None,event_ids=[payload['batch_events'][0]['event_id']],lesson_text=None,reason='Offline fixture: existing rules already cover the event.')])
        else:
            output=dict(item_id=payload['item']['item_id'],scores={k:2 if self.low and k=='clarity' else 4 for k in ('persona_fit','clarity','actionability','factual_grounding')},total_score=14 if self.low else 16,critical_violation=False)
        if role not in ('gate','evaluator'):m.rt.parse(role,json.dumps(output),payload)
        start=dict(key=key,role=role,payload=payload,request=request,metadata=meta,created_at=m.rt.utc(),reserved_usd=.01,
                   parent_sha256={p:m.digest(m.W/'results'/f'{p}.json') for p in parents})
        m.put(m.W/'started'/f'{key}.json',start)
        row=dict(key=key,role=role,status='success',output=output,cost_usd=.001,budget_charge_usd=.001,task_id=meta.get('task_id'),metadata=meta)
        with self.telemetry.attempt(key,role,payload,{},request,meta) as obs:
            m.put(m.W/'results'/f'{key}.json',row);obs.finish(row)
        self.calls.append((key,role,payload,meta));return row


def test_full_125_natural_and_125_mixed_requests_and_no_paid_calls(workspace):
    plan,path=workspace;r=Fake(plan);register=[];history=[];parent=None
    for batch in range(1,5):
        records=[r.task(t,register,parent) for t in plan['tasks'] if t['batch_id']==batch]
        closed=r.close_batch(batch,records,register,history)
        register,history,parent=closed['register'],closed['history'],closed['memory_parent']
    assert len(list((path/'tasks').glob('SE-FINAL-N*.json')))==125
    natural_calls=len(r.calls)
    assert sum(role=='memory' for _,role,_,_ in r.calls)==4
    assert not r.telemetry.receipt()['errors']
    entries=m.prepare_mixed(plan)
    assert sum(t['condition']=='unchanged' for t in entries)==73
    for typ in m.read(path/'execution_plan.json')['mixed_assignment'].values():assert 'defect_type' in typ
    for entry in entries:
        source=m.read(path/'tasks'/f"{entry['source_task_id']}.json")
        if entry['condition']=='unchanged':assert entry['initial']==source['initial']
        else:assert entry['initial']['body']!=source['initial']['body']
        result=r.task(entry)
        assert len(result['cycles'])==1 and result['evaluation_reused']
    assert len(list((path/'tasks').glob('SE-FINAL-M*.json')))==125
    assert set(role for _,role,_,_ in r.calls[natural_calls:])=={'gate','critic','optimizer','evaluator'}
    before=len(r.calls)
    for t in plan['tasks']:r.task(t)
    assert len(r.calls)==before
    assert m.prepare_mixed(plan)==entries
    manifest=m.read(path/'mixed_inputs.json');manifest['items'][0]['initial']['body']+='tampering'
    (path/'mixed_inputs.json').write_text(json.dumps(manifest),encoding='utf-8')
    with pytest.raises(RuntimeError,match='contents changed'):m.prepare_mixed(plan)


def test_max_two_repairs_keeps_low_quality_and_never_chases_pass(workspace):
    plan,path=workspace;r=Fake(plan,second=True,low=True)
    result=r.task(plan['tasks'][0])
    assert result['status']=='complete' and len(result['cycles'])==2
    assert result['operational_route']=='needs_human_review'
    assert result['final_eval']['scores']['clarity']==2
    assert sum(role=='optimizer' for _,role,_,_ in r.calls)==2
    assert sum(role=='evaluator' for _,role,_,_ in r.calls)==2


def test_replay_after_evaluation_failure_does_not_regenerate(workspace,monkeypatch):
    plan,path=workspace;r=Fake(plan)
    original=r.once
    def interrupt(key,role,*args):
        if role=='evaluator':raise RuntimeError('simulated evaluator outage')
        return original(key,role,*args)
    monkeypatch.setattr(r,'once',interrupt)
    with pytest.raises(RuntimeError,match='simulated evaluator'):r.task(plan['tasks'][0])
    checkpoint=m.read(path/'production'/f"{plan['tasks'][0]['task_id']}.json")
    assert checkpoint['execution_status']=='complete' and checkpoint['measurement_status']=='pending'
    assert not (path/'tasks'/f"{plan['tasks'][0]['task_id']}.json").exists()
    r=Fake(plan)
    result=r.task(plan['tasks'][0])
    assert result['status']=='complete'
    assert r.calls and all(role=='evaluator' for _,role,_,_ in r.calls)


def test_real_attempt_store_budget_and_export_failure_no_duplicate(workspace):
    plan,path=workspace
    tel=m.Telemetry('offline-store',client=FakeClient(fail='update'));tel.healthcheck()
    task=plan['tasks'][0];pp=m.p.planner_input(task,[])
    pl=dict(steps=[dict(instruction='Suggest a manual check.')])
    rp=m.p.research_input(task,pl,[]);work=dict(task,research=rp)
    payload=m.p.production(work,'writer',plan=pl,ledger={'ledger':[]})
    out=dict(item_id=payload['item_id'],title='Saved response',body='A'*1300)
    raw=dict(model=plan['templates']['writer']['candidate']['model'],status='completed',usage=dict(input_tokens=100,output_tokens=100),id='offline-response')
    calls=[]
    def create(**kw):
        calls.append(kw)
        return SimpleNamespace(model_dump=lambda **_:raw,output_text=json.dumps(out))
    r=m.Runner(dict(plan,minimum_provider_interval_seconds=0),{'openai':SimpleNamespace(responses=SimpleNamespace(create=create))},tel)
    r.context.set(dict(task_id=task['task_id'],batch_id=1,cohort='natural'))
    with tel.task(task['task_id']):
        got,key=r.call(task['task_id']+'_writer','writer',payload)
        got2,key2=r.call(task['task_id']+'_writer','writer',payload)
    assert got==got2==out and key==key2 and len(calls)==1
    assert tel.receipt()['errors'] and m.read(path/'results'/f'{key}.json')['status']=='success'
    r.plan['cap_usd']=r.charge
    with tel.task(task['task_id']):
        with pytest.raises(m.rt.StopRun,match='budget_limit'):r.once('BUDGET-GUARD','writer',payload,[])
    assert not (path/'started/BUDGET-GUARD.json').exists()


def test_interrupted_unknown_retains_accounting_metadata(workspace):
    plan,path=workspace
    m.put(path/'started/SE-FINAL-N001_writer__a001.json',dict(key='SE-FINAL-N001_writer__a001',role='writer',reserved_usd=.1,
        created_at='2026-09-07T08:00:00Z',metadata=dict(task_id='SE-FINAL-N001',batch_id=1,cohort='natural')))
    r=m.Runner(plan,{},m.Telemetry('offline',enabled=False))
    assert r.charge==.1 and r.records[0]['cost_usd'] is None
    assert r.records[0]['task_id']=='SE-FINAL-N001' and r.records[0]['cohort']=='natural'


def test_defect_fallback_is_frozen_and_deterministic():
    from defects import mutate
    original=dict(title='Fixed title',body='x'*150)
    a=mutate(original,'incoherent',0,'one topic');b=mutate(original,'incoherent',0,'one topic')
    assert a==b and a['modified']['body']!=original['body'] and 150<=len(a['modified']['body'])<=2000


def test_no_live_execution_without_registration(workspace):
    with pytest.raises(FileNotFoundError):m.verify_live()


def test_freeze_source_parity_and_archived_operational_recovery(workspace,monkeypatch):
    plan,path=workspace;code=path/'code';code.mkdir()
    sources=[code/name for name in ('run.py','telemetry.py','defects.py')]
    for src in sources:src.write_text('# original\n',encoding='utf-8')
    monkeypatch.setattr(m,'HERE',code);monkeypatch.setattr(m,'ROOT',path)
    monkeypatch.setattr(m,'source_files',lambda:sources)
    monkeypatch.setattr(m,'prepare',lambda:plan)
    def fresh_receipt():
        receipt=dict(passed=True,plan_sha256=m.digest(path/'execution_plan.json'),
            tested_runtime_sha256=m.digest(code/'run.py'),source_sha256={f.relative_to(path).as_posix():m.digest(f) for f in sources})
        (path/'offline_test_receipt.json').write_text(json.dumps(receipt),encoding='utf-8')
    fresh_receipt();(code/'run.py').write_text('# before freeze correction\n',encoding='utf-8')
    with pytest.raises(RuntimeError,match='Source changed after'):m.freeze()
    fresh_receipt();frozen=m.freeze()
    m.put(path/'registration.json',dict(freeze_sha256=m.digest(path/'freeze.json')))
    assert m.verify_live()==plan
    (code/'run.py').write_text('# equivalent operational recovery\n',encoding='utf-8')
    with pytest.raises(RuntimeError,match='Frozen source changed'):m.verify_live()
    fresh_receipt();m.record_recovery('serialization','Offline fixture: equivalent serialization correction')
    assert m.verify_live()==plan
    patch=m.read(next((path/'patches').glob('*.json')))
    change=patch['changes']['code/run.py']
    assert '-# before freeze correction' in change['unified_diff']
    assert '+# equivalent operational recovery' in change['unified_diff']
    assert m.digest(path/'source_archive'/change['old_sha256'])==change['old_sha256']
    (code/'defects.py').write_text('# changed scientific manipulation\n',encoding='utf-8')
    fresh_receipt()
    with pytest.raises(RuntimeError,match='Only equivalent'):m.record_recovery('serialization','Rejected scientific change')
