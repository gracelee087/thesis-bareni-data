"""Resumable real-workflow pilot. Immutable attempts; shared in-flight budget."""
import argparse, copy, importlib.util, json, os, re, subprocess, sys, threading, time, traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

S=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('connected_runtime',S/'tools/connected_pipeline_v1/runtime.py')
rt=importlib.util.module_from_spec(spec);sys.modules[spec.name]=rt;spec.loader.exec_module(rt)
W=S/'private/pilot125_v1';rt.W=W
read,save,digest,sha=rt.read,rt.save,rt.digest,rt.sha
D=S.parent/'study_d'

def put(path,value):
    if path.exists():
        if read(path)!=value:raise RuntimeError('Immutable checkpoint differs: '+str(path))
    else:save(path,value)

def prepare():
    selected=read(W/'selected_topics.json')
    persona=(D/'config/persona_experiment.md').read_text(encoding='utf-8')
    evidence=(D/'config/company_evidence.md').read_text(encoding='utf-8')
    config=json.loads(subprocess.check_output(['git','show','HEAD:studies/study_d/config/experiment.json'],cwd=S.parents[1]).decode())
    put(W/'study_d_experiment_snapshot.json',config)
    sources=[dict(source_id=f'C{n:02}',status='approved',text='## '+part.strip()) for n,part in enumerate(evidence.split('\n## ')[1:],1)]
    tasks=[];offset=0
    focuses=['problem_awareness','workflow_diagnosis','evidence_and_boundary','owner_decision_rule','bounded_next_step']
    for batch,size in enumerate(config['batch_sizes'],1):
        for local in range(1,size+1):
            index=offset+local;entry=selected['items'][index-1]
            # Same complete 25-cell CF/PF cycle as Study D, indexed from 1 for this new pilot.
            brief=(f"FROZEN PERSONA\n{persona}\n\nAPPROVED TASK\n**Audience:** CEO of a 1-10-person small business.\n"
                f"**Owner-specified abstract topic:** {entry['abstract_topic']}\n"
                "**Task:** Turn the abstract topic into a bounded Bareni workflow decision. Explain one practical next step.\n"
                f"**Format pattern:** CF-{((index-1)//5)%5+1:02}.\n**Persona focus:** PF-{(index-1)%5+1:02}_{focuses[(index-1)%5]}.\n"
                "**Evidence boundary:** Use only approved Bareni evidence. Do not invent customers, deployments, outcomes, savings, capabilities, or a multi-person team.\n"
                "**CTA rule:** None.\n**Output:** English LinkedIn post; body target 300-450 characters, hard range 150-600; title stored separately.")
            required=['Address the owner-specified topic as one concrete, bounded workflow decision.','Explain one practical next step for the owner.']
            prohibited=['No invented customer, deployment, result, number, capability, multi-person team, or sales CTA.','No autonomous money movement or high-risk decision; no excluded service.']
            preserve=['Preserve the frozen persona, approved evidence status, and human approval boundaries.','Use plain English; keep examples or proposals distinct from existing capabilities or observed results.']
            research=dict(company_evidence=sources,task_evidence=[dict(source_id='S01',status='approved',text='Owner-authorized task instructions (not evidence of business outcomes): '+brief)],constraints=[dict(constraint_id=f'K{n:02}',text=v) for n,v in enumerate(prohibited+preserve,1)])
            tasks.append(dict(task_id=f'SE-PILOT-{index:03}',index=index,local=local,batch_id=batch,topic=entry,brief=brief,required=required,prohibited=prohibited,preserve=preserve,research=research))
        offset+=size
    plan=dict(created_at=rt.utc(),authorization='User: full permission, cumulative below USD50; real-workflow pilot125; fix operational failures and resume to completion.',cap_usd=49.99,prior_budget_charge_usd=read(S/'private/connected_pipeline_v1/summary.json')['cumulative_budget_charge_usd'],templates=rt.templates(),tasks=tasks,batch_sizes=config['batch_sizes'],workers=4,request_timeout_seconds=180,max_calls=4000,max_refinements=2,schema_retry_limit=12,transport_retry_limit=7,max_register_entries=12,max_proposals=3,representative_failures_max=5,independent_initial_final=True,identical_text_evaluation_reuse=True,sdk_versions=rt.api.versions(),policy='Exploratory integration pilot, not confirmatory. Keep tested Study E role prompts/contracts/model settings and gate/evaluator rubric. Inherit Study D persona/evidence/brief pattern, unconditional first refinement, at most two refinements, full register to Planner and only selected lessons to Researcher/Writer; batch-only memory updates. No outcome-based stopping or forced pass. Unresolved output is recorded as needs_human_review, without requiring manual grading to complete pilot. Technical errors preserve attempts and retry; repeated failure pauses for an operational patch. Initial and final independent evaluations never reach production agents. No prior lessons or outcome records as model input.',source_sha256={str(p.relative_to(S.parents[1])):digest(p) for p in [Path(__file__),S/'tools/connected_pipeline_v1/runtime.py',D/'config/persona_experiment.md',D/'config/company_evidence.md',D/'src/b2_final/prompts.py',D/'src/b2_final/sources.py',D/'src/b2_final/memory.py',W/'selected_topics.json',W/'topic_inventory.json']},role_source_sha256=rt.source_snapshot())
    put(W/'execution_plan.json',plan)
    print(json.dumps(dict(prepared=125,batches=config['batch_sizes'],cap=49.99,prior=plan['prior_budget_charge_usd'])))

def planner_input(task,register):
    r=task['research']
    return dict(role='planner',item_id=f"E-PLAN-5{task['local']:02}",brief=task['brief'],company_evidence=r['company_evidence'],task_evidence=r['task_evidence'],constraints=r['constraints'],requirements=[dict(requirement_id=f'R{n:02}',text=v) for n,v in enumerate(task['required'],1)],lesson_register=[dict(lesson_id=x['lesson_id'],text=x['text']) for x in register])

def research_input(task,plan,selected):
    p=copy.deepcopy(task['research']);p.update(role='researcher',item_id=f"E-RES-6{task['local']:02}",brief=task['brief']+'\nClassify each planned instruction as supplied; instructions are proposals, not proof of existing implementation. Selected prior lessons (guidance, not factual evidence): '+json.dumps(selected,ensure_ascii=False),claims=[dict(claim_id=f'Q{n:02}',text=step['instruction']) for n,step in enumerate(plan['steps'],1)])
    return p

def production(task,role,**kwargs):
    t=dict(task,label='A');p=rt.production_input(t,role,**kwargs)
    p['item_id']=f"E-{'WRITE-3' if role=='writer' else 'OPT-4'}{task['local']:02}"
    return p

class Runner:
    def __init__(self,plan,clients):
        self.plan=plan;self.clients=clients;self.lock=threading.Lock();self.freeze=digest(W/'execution_plan.json');self.records=[];self.charge=plan['prior_budget_charge_usd'];self.inflight=0
        for path in sorted((W/'started').glob('*.json')):
            result=W/'results'/path.name
            if result.exists():row=read(result)
            else:
                start=read(path);row=dict(key=start['key'],role=start['role'],status='interrupted_unknown',budget_charge_usd=start['reserved_usd'],cost_usd=None,output=None)
                save(result,row)
            self.records.append(row);self.charge+=row['budget_charge_usd']

    def once(self,key,role,p,parents):
        if role=='evaluator':
            kw=p['request'];c=dict(provider='google',model='gemini-3.8-flash',input=.75,cached_input=.075,cache_write_input=.75,output=3.75)
            reserved=((len(json.dumps(kw,ensure_ascii=False).encode())+4096)*.75+4096*3.75)/1e6
        else:
            t=self.plan['templates'][role];c=t['candidate'];kw=rt.request_for(role,p,t);reserved=rt.api.reserve(c,kw,kw.get('max_tokens',kw.get('max_output_tokens')))
        with self.lock:
            if len(self.records)+self.inflight>=self.plan['max_calls']:raise rt.StopRun('call_limit')
            if self.charge+reserved>self.plan['cap_usd']:raise rt.StopRun('budget_limit')
            for k in parents:
                if read(W/'results'/(k+'.json'))['status']!='success':raise RuntimeError('Invalid parent '+k)
            start=dict(created_at=rt.utc(),key=key,role=role,payload=p,request=kw,request_sha256=sha(kw),reserved_usd=reserved,freeze_sha256=self.freeze,parent_sha256={k:digest(W/'results'/(k+'.json')) for k in parents},candidate=c,runtime_sha256=digest(Path(__file__)))
            save(W/'started'/(key+'.json'),start);self.charge+=reserved;self.inflight+=1
        begin=time.perf_counter();response=None
        row=dict(status='transport_failure',usage=None,cost_usd=None,output=None,raw_text=None,provider_response=None)
        try:
            if role=='evaluator':response=self.clients['google'].models.generate_content(**kw)
            elif c['provider']=='openai':response=self.clients['openai'].responses.create(**kw)
            else:response=self.clients['anthropic'].messages.create(**kw)
            raw=response.model_dump(mode='json');row['provider_response']=raw
            if role=='evaluator':row.update(rt.check_evaluator(response,p['item']))
            elif role=='gate':
                checked=rt.api.validate_response(response,c['provider'],c,p);row.update(checked);row['output']=checked['rating']
            else:
                row['status']='usage_failure';row['usage'],row['cost_usd']=rt.api.usage_and_cost(c['provider'],raw,c)
                actual=raw.get('model','')
                if not (actual==c['model'] or (c['provider']=='openai' and re.fullmatch(re.escape(c['model'])+r'-\d{4}-\d{2}-\d{2}',actual))):raise rt.StopRun('model_mismatch')
                stop=raw.get('status') if c['provider']=='openai' else raw.get('stop_reason')
                row['raw_text']=response.output_text if c['provider']=='openai' else ''.join(b.text for b in response.content if b.type=='text')
                row['status']='validation_failure'
                if stop!=('completed' if c['provider']=='openai' else 'end_turn'):raise ValueError('incomplete_response')
                row['output']=rt.parse(role,row['raw_text'],p)
                if role=='critic':
                    needed=set(rt.cm.target_ids(p));covered={k for repair in row['output']['repairs'] for k in repair['target_ids']}
                    if not needed<=covered:raise ValueError('unaddressed_gate_defect')
                if role=='memory':rt.project(row['output'],p)
                row.update(status='success',stop_reason=stop)
        except Exception as exc:
            # Provider exception text can contain credentials; retain safe metadata only.
            row.update(error_kind=type(exc).__name__,http_status=getattr(exc,'status_code',None))
            if isinstance(exc,ValueError):row['validation_detail']=str(exc)[:800]
            if isinstance(exc,rt.StopRun):row['status']=str(exc)
        row.update(key=key,role=role,freeze_sha256=self.freeze,latency_ms=round((time.perf_counter()-begin)*1000),budget_charge_usd=row['cost_usd'] if row['cost_usd'] is not None else reserved)
        with self.lock:
            save(W/'results'/(key+'.json'),row);self.records.append(row);self.charge+=row['budget_charge_usd']-reserved;self.inflight-=1
            print(json.dumps(dict(call=len(self.records),key=key,status=row['status'],charge_with_inflight=round(self.charge,6))),flush=True)
        return row

    def call(self,logical,role,p,parents=()):
        previous=sorted((W/'started').glob(logical+'__a*.json'))
        for path in previous:
            start=read(path);row=read(W/'results'/path.name)
            if start['payload']!=p or set(start['parent_sha256'])!=set(parents):raise RuntimeError('Resume input changed: '+logical)
            if row['status']=='success':return row['output'],row['key']
        for attempt in range(len(previous)+1,self.plan['schema_retry_limit']+1):
            key=f'{logical}__a{attempt:02}';row=self.once(key,role,p,parents)
            if row['status']=='success':return row['output'],key
            if row['status']=='model_mismatch':raise rt.StopRun('model_mismatch')
            if row.get('http_status') in (400,401,403,404):raise rt.StopRun('provider_configuration_error: '+key)
            if row['status']=='transport_failure' and attempt>=self.plan['transport_retry_limit']:break
            time.sleep(min(2**min(attempt,4),16))
        raise rt.StopRun('retry_exhausted: '+logical)

    def task(self,t,register,memory_parent=None):
        key=t['task_id'];outpath=W/'tasks'/(key+'.json')
        if outpath.exists():return read(outpath)
        pp=planner_input(t,register);pl,pk=self.call(key+'_planner','planner',pp,[memory_parent] if memory_parent else [])
        ids={x['lesson_id'] for x in pl['selected_lessons']};selected=[x for x in register if x['lesson_id'] in ids]
        rp=research_input(t,pl,selected);research,rk=self.call(key+'_researcher','researcher',rp,[pk])
        work=copy.deepcopy(t);work['research']=rp
        wp=production(work,'writer',plan=pl,ledger=research)
        wp['fixed_plan'].append('Only Planner-selected lessons (guidance, not evidence): '+json.dumps(selected,ensure_ascii=False))
        first,wk=self.call(key+'_writer','writer',wp,[pk,rk]);draft=first;draft_key=wk
        gp=rt.gate_input(work,draft,f"GATE-BLIND-{t['index']:03}",self.plan['templates']['gate']['rules'])
        initial,gk=self.call(key+'_gate0','gate',gp,[wk]);assessment=initial;cycles=[]
        for cycle in (1,2):
            cp=rt.critic_input(work,draft,assessment,gp,f'E-CRIT-{key}-{cycle}')
            critique,ck=self.call(key+f'_critic{cycle}','critic',cp,[draft_key,gk])
            op=production(work,'optimizer',draft=draft,repairs=critique,cycle=cycle)
            # Restore original plan/ledger to Optimizer using its existing fixed-critique list interface.
            op['fixed_critique'].append('Preserve original Planner guidance and Researcher restrictions: '+json.dumps(dict(plan=pl,ledger=research),ensure_ascii=False))
            draft,draft_key=self.call(key+f'_optimizer{cycle}','optimizer',op,[draft_key,ck,rk])
            gp=rt.gate_input(work,draft,f"GATE-BLIND-{t['index']:03}",self.plan['templates']['gate']['rules'])
            assessment,gk=self.call(key+f'_gate{cycle}','gate',gp,[draft_key])
            cycles.append(dict(cycle=cycle,critique=critique,gate=assessment,draft=draft,gate_key=gk))
            if not assessment['defects']:break
        # Blinded measurement after production ends; never used for routing or lessons.
        ep=rt.evaluator_input(work,first,f"EVAL-BLIND-{t['index']:03}")
        initial_eval,iek=self.call(key+'_eval_initial','evaluator',ep,[wk])
        identical=all(first[k]==draft[k] for k in ('title','body'))
        if identical:final_eval,fek=initial_eval,iek
        else:final_eval,fek=self.call(key+'_eval_final','evaluator',rt.evaluator_input(work,draft,f"EVAL-BLIND-{t['index']:03}"),[draft_key])
        result=dict(task_id=key,batch_id=t['batch_id'],topic=t['topic']['abstract_topic'],status='complete',operational_route='needs_human_review' if assessment['defects'] else 'release_candidate',initial=first,final=draft,initial_gate=initial,final_gate=assessment,cycles=cycles,initial_eval=initial_eval,final_eval=final_eval,evaluation_reused=identical,evaluation_keys=[iek,fek],planner=pl,researcher=research,selected_lessons=selected,register_sha256=sha(register),research_diagnostics=rt.pr.observable_checks(research,rp),final_key=draft_key,final_gate_key=gk)
        put(outpath,result);print(json.dumps(dict(completed=key,batch=t['batch_id'],route=result['operational_route'])),flush=True);return result

    def close_batch(self,batch,records,register,history):
        path=W/'batches'/f'batch_{batch}.json'
        if path.exists():return read(path)
        failures=[r for r in records if r['initial_gate']['defects']]
        failures.sort(key=lambda r:(not bool(r['final_gate']['defects']),not any(d['severity']=='critical' for d in r['initial_gate']['defects']),r['task_id']))
        summary=dict(batch=batch,observed=len(records),initial_failed=len(failures),final_unresolved=sum(bool(r['final_gate']['defects']) for r in records),refined=len(records),representative_task_ids=[r['task_id'] for r in failures[:5]])
        events=[dict(event_id=f'B{batch}-SUMMARY',status='confirmed',observation='Confirmed execution-log summary; Gate findings are model reports, not independently established business facts. '+json.dumps(summary))]
        for r in failures[:5]:
            events.append(dict(event_id=r['task_id'],status='confirmed',observation='Recorded Gate finding and repair outcome, not a customer outcome: '+json.dumps(dict(task_id=r['task_id'],topic=r['topic'],initial_gate=r['initial_gate'],final_gate=r['final_gate'],critic_excerpt=json.dumps(r['cycles'][0]['critique'],ensure_ascii=False)[:500]),ensure_ascii=False)))
        mp=dict(role='memory',item_id=f'E-MEM-BATCH-{batch}',brief='Propose at most three reusable lessons from the bounded batch Gate failure summary. ADD only a new pattern; MERGE duplicate prevention/scope; SKIP rules already imposed by the frozen persona, evidence boundary or task contract. Preserve historical provenance. A confirmed event confirms a recorded model report, not the truth of every model judgement. No independent outcome scores are supplied. Frozen persona: '+(D/'config/persona_experiment.md').read_text(encoding='utf-8'),company_evidence=self.plan['tasks'][0]['research']['company_evidence'],lesson_register=register,history_events=history,batch_events=events,max_register_entries=12,max_proposals=3)
        memory,mk=self.call(f'batch{batch}_curator','memory',mp,[r['final_gate_key'] for r in records])
        updated=rt.project(memory,mp);result=dict(batch=batch,summary=summary,events=events,register_before_sha256=sha(register),register=updated,curator=memory,memory_parent=mk,history=history+events)
        put(path,result);return result

def run():
    plan=read(W/'execution_plan.json')
    assert plan['sdk_versions']==rt.api.versions(),'SDK changed'
    # Frozen scientific inputs; runtime changes require an explicit patch receipt.
    for rel,expected in plan['source_sha256'].items():
        path=S.parents[1]/rel
        if path==Path(__file__):continue
        assert digest(path)==expected,'Frozen source changed: '+rel
    if digest(Path(__file__))!=plan['source_sha256'][str(Path(__file__).relative_to(S.parents[1]))]:
        assert any(read(p).get('new_runtime_sha256')==digest(Path(__file__)) for p in (W/'patches').glob('*.json')),'Unrecorded runtime patch'
    assert read(W/'offline_test_receipt.json')['passed']
    lockpath=S/'private/role_selection_budget.lock'
    with lockpath.open('x',encoding='utf-8') as budgetlock:
        budgetlock.write('pilot125_v1');budgetlock.flush()
        clients={};runner=None;reason=None
        try:
            clients=rt.api.create_clients(plan)
            from google import genai
            from google.genai import types
            clients['google']=genai.Client(api_key=os.environ['GOOGLE_API_KEY'],http_options=types.HttpOptions(timeout=180000,retry_options=types.HttpRetryOptions(attempts=1)))
            runner=Runner(plan,clients);register=[];history=[];parent=None
            for batch in range(1,5):
                tasks=[t for t in plan['tasks'] if t['batch_id']==batch]
                with ThreadPoolExecutor(max_workers=plan['workers']) as pool:
                    futures=[pool.submit(runner.task,t,copy.deepcopy(register),parent) for t in tasks]
                    try:records=[f.result() for f in as_completed(futures)]
                    except Exception:
                        for f in futures:f.cancel()
                        raise
                records.sort(key=lambda r:r['task_id']);closed=runner.close_batch(batch,records,register,history)
                register,history,parent=closed['register'],closed['history'],closed['memory_parent']
        except Exception as exc:
            reason=str(exc);traceback.print_exc()
        finally:
            if runner:
                completed=list((W/'tasks').glob('*.json'));rows=runner.records
                summary=dict(created_at=rt.utc(),status='complete' if reason is None and len(completed)==125 else 'paused',stop_reason=reason,completed_tasks=len(completed),actual_calls=len(rows),valid_calls=sum(r['status']=='success' for r in rows),known_new_cost_usd=round(sum(r['cost_usd'] or 0 for r in rows),8),unknown_new_reserved_usd=round(sum(r['budget_charge_usd'] for r in rows if r['cost_usd'] is None),8),cumulative_budget_charge_usd=round(runner.charge,8),cap_usd=plan['cap_usd'])
                save(W/'sessions'/f"session_{time.time_ns()}.json",summary)
                (W/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
                print(json.dumps(summary),flush=True)
            for client in clients.values():client.close()
            budgetlock.close();lockpath.unlink()
    if reason:raise SystemExit(1)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['prepare','execute']);args=parser.parse_args()
    prepare() if args.command=='prepare' else run()
