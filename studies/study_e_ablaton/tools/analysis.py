"""Separate ablation analysis; never imports STUDY-E-1 outcome scores."""
import argparse
import json
from pathlib import Path
import numpy as np
from scipy.stats import t
from experiment import STUDY_ID, DIMENSIONS

def analyze(rows, task_ids, repeats=3, draws=100000, seed=2026090802):
    expected={(i,r,a) for i in task_ids for r in range(1,repeats+1) for a in ('critic_on','critic_off')}
    values={};seen=set()
    for row in rows:
        if row.get('study_id')!=STUDY_ID:
            raise ValueError('wrong_study')
        key=(row['item_id'],row['repeat'],row['arm'])
        if key not in expected or key in seen:
            raise ValueError('unexpected_or_duplicate_observation')
        seen.add(key)
        if row.get('status')!='complete':
            continue
        scores=row.get('scores',{})
        if set(scores)!=set(DIMENSIONS) or any(type(v) is not int or not 1<=v<=5 for v in scores.values()):
            raise ValueError('invalid_scores')
        values[key]=sum(scores.values())
    missing=sorted(expected-set(values))
    base=dict(study_id=STUDY_ID,n_source_tasks=len(task_ids),repeats=repeats,
              planned_outputs=len(expected),valid_outputs=len(values),missing=missing)
    if missing:
        return dict(base,status='incomplete_no_primary_test')
    differences=np.array([[values[(i,r,'critic_on')]-values[(i,r,'critic_off')]
                           for r in range(1,repeats+1)] for i in task_ids],dtype=float)
    task_means=differences.mean(axis=1)
    observed=float(task_means.mean())
    rng=np.random.default_rng(seed); extreme=0
    for start in range(0,draws,2000):
        signs=rng.integers(0,2,size=(min(2000,draws-start),len(task_ids)))*2-1
        permuted=(signs*task_means).mean(axis=1)
        extreme+=int(np.count_nonzero(np.abs(permuted)>=abs(observed)-1e-12))
    se=float(task_means.std(ddof=1)/np.sqrt(len(task_ids))) if len(task_ids)>1 else None
    margin=float(t.ppf(.975,len(task_ids)-1)*se) if se is not None else None
    return dict(base,status='complete',mean_difference_on_minus_off=observed,
        task_mean_differences=dict(zip(task_ids,task_means.tolist())),
        paired_randomization=dict(p_two_sided=(extreme+1)/(draws+1),draws=draws,seed=seed,
             unit='source task; all repeat differences jointly sign-flipped',
             assumptions='Sharp no-treatment-effect null; randomized arm order and no cross-arm interference; fixed imported inputs.'),
        reference_t_interval_95=[observed-margin,observed+margin] if margin is not None else None,
        interval_limit='Reference only; does not model shared source-context dependence or justify population generalization.',
        minimum_interest_difference=.5,
        inference_scope='New controlled comparison on fixed known mixed inputs, not the original study or architecture as a whole.')

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--rows',type=Path,required=True)
    parser.add_argument('--inputs',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    rows=json.loads(args.rows.read_text(encoding='utf-8'))
    tasks=json.loads(args.inputs.read_text(encoding='utf-8'))['items']
    result=analyze(rows,[x['item_id'] for x in tasks])
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x',encoding='utf-8') as out:json.dump(result,out,ensure_ascii=False,indent=2)
