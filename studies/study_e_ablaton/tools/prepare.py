"""Read-only source import and deterministic preparation. No API or credentials."""
import hashlib
import json
import math
import random
from pathlib import Path
from experiment import STUDY_ID, OPTIMIZER_INSTRUCTION

BASE=Path(__file__).resolve().parents[1]
ROOT=BASE.parents[1]
SOURCE=ROOT/'studies/study_e_redesign/private/final125_v1'
DEST=BASE/'private'

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def put(path,value):
    if path.exists():
        if read(path)!=value:
            raise RuntimeError('Refusing to overwrite different prepared artifact: '+path.name)
        return
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8') as out:
        json.dump(value,out,ensure_ascii=False,indent=2)
        out.write('\n')

def main():
    assert not DEST.resolve().is_relative_to(SOURCE.resolve())
    plan=read(SOURCE/'execution_plan.json'); mixed=read(SOURCE/'mixed_inputs.json')['items']
    assert len(mixed)==125 and len({x['source_task_id'] for x in mixed})==125
    assert sum(x['condition']=='unchanged' for x in mixed)==73
    source_paths=[SOURCE/'execution_plan.json',SOURCE/'mixed_inputs.json',SOURCE/'pricing.json']
    source_paths.extend(SOURCE/'tasks'/f"{x['source_task_id']}.json" for x in mixed)
    before={str(p.relative_to(ROOT)):digest(p) for p in source_paths}
    tasks={x['task_id']:x for x in plan['tasks']}; items=[]
    for i,m in enumerate(mixed,1):
        original=read(SOURCE/'tasks'/f"{m['source_task_id']}.json")
        t=tasks[m['source_task_id']]
        context=dict(task={k:t[k] for k in ('brief','required','prohibited','preserve','research')},
                     planner=original['planner'],researcher=original['researcher'],
                     selected_lessons=original['selected_lessons'])
        items.append(dict(item_id=f'SEA-I{i:03}',source_mixed_task_id=m['task_id'],
                          source_natural_task_id=m['source_task_id'],stratum=m['condition'],
                          initial={k:m['initial'][k] for k in ('title','body')},context=context))
    put(DEST/'inputs.json',dict(study_id=STUDY_ID,items=items))
    rng=random.Random(2026090801)
    pairs=[]
    for item in items:
        for rep in range(1,4):
            arms=['critic_on','critic_off'];rng.shuffle(arms)
            pairs.append(dict(pair_id=f"{item['item_id']}-R{rep}",item_id=item['item_id'],
                              repeat=rep,arm_order=arms,content_id=f'POST-{rng.getrandbits(96):024x}'))
    rng.shuffle(pairs)
    evaluations=[]
    for pair in pairs:
        for arm in ('critic_on','critic_off'):
            evaluations.append(dict(blind_id=f'EVAL-{rng.getrandbits(128):032x}',pair_id=pair['pair_id'],arm=arm))
    rng.shuffle(evaluations)
    put(DEST/'schedule.json',dict(study_id=STUDY_ID,seed=2026090801,pairs=pairs,evaluation_order=evaluations))
    # Original templates are provenance only: their old user messages are not new inputs.
    roles={k:dict(candidate=v['candidate'],system=v['system'],request_settings={a:b for a,b in v['request'].items() if a not in ('input','messages','contents','system')})
           for k,v in plan['templates'].items() if k in ('gate','critic','optimizer')}
    roles['optimizer']['system']=OPTIMIZER_INSTRUCTION
    put(DEST/'role_configuration.json',dict(study_id=STUDY_ID,roles=roles,
        evaluator=dict(provider='google',model='gemini-3.8-flash',status='request_adapter_pending')))
    summary=read(SOURCE/'reports_final_2026-09-08/mixed_analysis.json')
    means={r:v['per_attempt_known_cost_descriptive_usd']['mean'] for r,v in summary['role_cost_ledger'].items()}
    estimates={}
    for cycles in (1,2):
        per_pair=(1+2*cycles)*means['gate']+cycles*means['critic']+2*cycles*means['optimizer']+2*means['evaluator']
        estimates[str(cycles)+'_cycles_both_arms']=dict(usd=375*per_pair,successful_calls=375*(1+5*cycles+2))
    put(DEST/'cost_estimate.json',dict(study_id=STUDY_ID,basis='Prior observed role means; new prompt length, retries and pricing may change cost. Not a cap or invoice.',
        source_summary_sha256=digest(SOURCE/'reports_final_2026-09-08/mixed_analysis.json'),estimates=estimates,
        approved_budget_cap_usd=None,current_price_verification='pending',repetitions=3,final_outputs=750))
    z=1.959963984540054+0.8416212335729143
    put(DEST/'sample_size_sensitivity.json',dict(study_id=STUDY_ID,method='Normal approximation for paired mean, not exact randomization-test power',
        alpha=.05,target_power=.8,minimum_difference=.5,planned_source_tasks=125,
        assumed_task_mean_difference_sd=[dict(sd=s,n_required=math.ceil((z*s/.5)**2)) for s in (1,2,3)],
        no_observed_ablation_effect_used=True))
    after={str(p.relative_to(ROOT)):digest(p) for p in source_paths}
    assert before==after
    put(DEST/'source_manifest.json',dict(study_id=STUDY_ID,source_study='STUDY-E-1',files=before,
        imported_fields='Initial mixed title/body and original task context only; no final output or evaluation scores'))
    put(DEST/'READINESS.json',dict(study_id=STUDY_ID,source_study_unchanged=True,input_count=125,
        transformed=52,unchanged=73,planned_pairs=375,planned_outputs=750,paid_model_calls=0,
        phase='prepared_not_frozen',external_preregistration=False,execution_started=False,
        remaining=['Budget cap and final repeat count','Live provider/telemetry/durable-resume adapter and tests',
                   'Blinded evaluator request adapter and tests','Analysis implementation and synthetic validation',
                   'Current model/pricing verification','Final plan freeze and registration status decision']))
    print(json.dumps(dict(study_id=STUDY_ID,inputs=len(items),pairs=len(pairs),outputs=len(evaluations),
                          estimates=estimates,source_hashes_unchanged=True,model_calls=0)))

if __name__=='__main__':
    main()
