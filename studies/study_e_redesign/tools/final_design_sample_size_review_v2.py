"""Offline sample-size scenarios for the final Study E numerical policy.

No sample-size decision, final-analysis change, provider calls, or observed-power
calculation. Pilot INITIAL levels only parameterize illustrative score scenarios.
"""
import argparse
import hashlib
import json
import math
import socket
import warnings
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import scipy
from scipy.stats import binom, norm, wilcoxon

ROOT = Path(__file__).resolve().parents[3]
S = ROOT / "studies/study_e_redesign"
FINAL = S / "private/final125_v1"
GRID = [75, 100, 125, 150, 200, 250, 500, 1000]
DRAWS = 20000
SEED = 202609071402

def no_network(*args, **kwargs):
    raise RuntimeError("Network prohibited during sample-size review")
socket.socket.connect = no_network
socket.create_connection = no_network

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def rng(label):
    return np.random.default_rng(np.random.SeedSequence(
        [SEED, int.from_bytes(hashlib.sha256(label.encode()).digest()[:8], "little")]))

def rate(events):
    p = float(np.mean(events))
    return dict(estimate=p, mc_se=math.sqrt(p*(1-p)/len(events)), draws=len(events))

def wilson(k, n):
    z = norm.ppf(.975)
    center = (k/n+z*z/(2*n))/(1+z*z/n)
    half = z*math.sqrt((k/n)*(1-k/n)/n+z*z/(4*n*n))/(1+z*z/n)
    return [float(center-half), float(center+half)]

def event_minimum(p, target):
    n = target
    while binom.sf(target-1, n, p) < .95:
        n += 1
    assert n == target or binom.sf(target-1, n-1, p) < .95
    return n

def signed_count_p(positive, negative):
    """Final asymptotic Pratt p-value specialized to -1/0/+1 differences."""
    m = positive+negative
    z = np.divide(positive-negative, np.sqrt(m), out=np.zeros_like(m, dtype=float), where=m>0)
    return 2*norm.sf(abs(z))

def exact_iid_rejection_grid(positive, negative, maximum=1000):
    """Exact rejection probabilities of an ASYMPTOTIC test, not exact-test power."""
    change = positive+negative
    conditional = np.zeros(maximum+1)
    for m in range(1, maximum+1):
        x = np.arange(m+1)
        rejected = signed_count_p(x, m-x) < .05
        conditional[m] = binom.pmf(x, m, positive/change)[rejected].sum()
    powers = []
    for n in range(1, maximum+1):
        powers.append(float(binom.pmf(np.arange(n+1), n, change) @ conditional[:n+1]))
    return powers

def score_probabilities(totals, repair, harm):
    # First decrease by one with probability harm if above the score floor;
    # otherwise increase by one with probability repair if below the ceiling.
    a = np.array(totals)
    negative = harm*float(np.mean(a>4))
    positive = repair*(float(np.mean(a<20))-harm*float(np.mean((a>4)&(a<20))))
    return positive, negative

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir', type=Path, default=S/'private/final_design_sample_size_review_v2')
    out = parser.parse_args().output_dir.resolve()
    receipt = json.loads((FINAL/'offline_test_receipt.json').read_text('utf-8'))
    sources = [ROOT/p for p in receipt['source_sha256']]
    sources += [S/'219_PROPOSAL_ONLY_ANALYSIS_DECISION.md',
                S/'private/proposal_only_pilot_analysis_v1/natural_proposal_analysis.json',
                S/'private/proposal_only_pilot_analysis_v1/mixed_proposal_analysis.json',
                Path(__file__).resolve()]
    before = {p.relative_to(ROOT).as_posix(): digest(p) for p in sources}
    assert all(before[p] == h for p,h in receipt['source_sha256'].items())
    assert not (FINAL/'freeze.json').exists()
    assert not list((FINAL/'started').glob('*.json'))
    assert not list((FINAL/'results').glob('*.json'))
    plan = json.loads((FINAL/'execution_plan.json').read_text('utf-8'))
    assert len(plan['tasks']) == 125 and len(plan['mixed_assignment']) == 52
    natural = json.loads(sources[-3].read_text('utf-8'))['items']
    mixed = json.loads(sources[-2].read_text('utf-8'))['items']
    assert len(natural) == len(mixed) == 125
    natural_initial = [x['initial_total'] for x in natural]
    strata = {}
    for item in mixed:
        strata.setdefault(item['stratum'], []).append(item['initial_total'])
    unchanged = next(k for k,v in strata.items() if len(v)==73)
    assert sorted(map(len,strata.values())) == [13,13,13,13,73]
    result = dict(created_at=datetime.now(timezone.utc).isoformat(), seed=SEED,
        draws=DRAWS, numpy=np.__version__, scipy=scipy.__version__, grid=GRID,
        status='CONDITIONAL_REVIEW_NOT_A_NEW_SAMPLE_SIZE_DECISION',
        source_sha256=before, final_check_id=receipt['check_id'],
        pilot_initial_context=dict(natural_mean=float(np.mean(natural_initial)),
          natural_ceiling=sum(x==20 for x in natural_initial),
          mixed_strata={k:dict(n=len(v),mean=float(np.mean(v)),ceiling=sum(x==20 for x in v)) for k,v in strata.items()}),
        h1=[], h2=[], event_availability=[], mixed_event_availability=[],
        iid_wilcoxon=[], mixed_wilcoxon=[], dependence=[], missingness=[])
    # Validate the count shortcut against the exact final SciPy test settings.
    g = rng('shortcut-validation')
    differences = g.choice([-1.,0.,1.], size=(1000,125), p=[.05,.85,.10])
    differences[0,:] = 0
    differences[1,:] = 1
    expected = np.ones(1000)
    nonzero = np.any(differences!=0, axis=1)
    expected[nonzero] = wilcoxon(differences[nonzero],axis=1,zero_method='pratt',
        alternative='two-sided',correction=False,method='asymptotic').pvalue
    actual = signed_count_p((differences>0).sum(axis=1),(differences<0).sum(axis=1))
    assert np.allclose(actual, expected, atol=1e-12)
    result['count_shortcut_validated_against_final_scipy'] = True

    for n in GRID:
        for p in [.90,.95]:
            k = math.ceil(n*p)
            result['h1'].append(dict(n=n,hypothetical_completions=k,
                hypothetical_wilson95=wilson(k,n),assumed_completion_probability=p,
                probability_observed_criterion=float(binom.sf(math.ceil(.9*n)-1,n,p))))
        for missing in [.001,.01]:
            result['missingness'].append(dict(n=n,assumed_task_level_unresolved_probability=missing,
                probability_all_tasks_resolved=(1-missing)**n))
        for p in [.024,.05,.10]:
            result['event_availability'].append(dict(n=n,assumed_initial_low=p,expected_events=n*p,
                probability_zero=float(binom.pmf(0,n,p)),probability_at_least_10=float(binom.sf(9,n,p)),
                probability_at_least_20=float(binom.sf(19,n,p))))
        # These two scaling choices are counterfactual design options, not edits.
        for allocation in ['fixed_52','approximately_fixed_fraction']:
            transformed = 52 if allocation=='fixed_52' else 4*round(n*(52/125)/4)
            for q in [.5,.8]:
                pmf=np.convolve(binom.pmf(np.arange(transformed+1),transformed,q),
                    binom.pmf(np.arange(n-transformed+1),n-transformed,.024))
                assert abs(pmf.sum()-1)<1e-10
                result['mixed_event_availability'].append(dict(n=n,allocation=allocation,transformed=transformed,
                    assumed_transformed_low=q,assumed_unchanged_low=.024,
                    expected_events=transformed*q+(n-transformed)*.024,
                    probability_at_least_20=float(np.clip(pmf[20:].sum(),0,1))))
        # Cost precision under declared lognormal scenarios, conditional on known costs.
        for cv in [.2,.25,.3]:
            g=rng(f'cost-{n}-{cv}'); measured=[]
            sigma=math.sqrt(math.log1p(cv*cv))
            for _ in range(DRAWS//1000):
                a=np.exp(-sigma*sigma/2+sigma*g.normal(size=(1000,n)))
                measured.extend(a.std(axis=1,ddof=1)/a.mean(axis=1))
            measured=np.array(measured)
            result['h2'].append(dict(n=n,assumed_population_cv=cv,
                sampling_95_range=list(map(float,np.quantile(measured,[.025,.975]))),
                observed_criterion=rate(measured<.25),
                probability_absolute_error_at_most_025=rate(abs(measured-cv)<=.025),
                probability_absolute_error_at_most_05=rate(abs(measured-cv)<=.05)))

    result['natural_event_minima']=[dict(p=p,n_for_95pct_at_least_10=event_minimum(p,10),
        n_for_95pct_at_least_20=event_minimum(p,20)) for p in [.024,.05,.10]]
    # Natural ceiling-aware iid scenarios. No observed pilot changes are used.
    for repair in [.25,.5,.8]:
        positive,negative=score_probabilities(natural_initial,repair,.01)
        powers=exact_iid_rejection_grid(positive,negative)
        null=exact_iid_rejection_grid((positive+negative)/2,(positive+negative)/2)
        first=next((n for n,p in enumerate(powers,1) if p>=.8),None)
        assert first is None or (powers[first-1]>=.8 and max(powers[:first-1],default=0)<.8)
        result['iid_wilcoxon'].append(dict(improve_if_eligible=repair,harm_probability=.01,
            positive_probability=positive,negative_probability=negative,
            expected_mean_change=positive-negative,first_n_at_80=first,
            rejection_at_first_n=powers[first-1] if first else None,
            rejection_at_previous_n=powers[first-2] if first and first>1 else None,
            maximum_rejection_before_first_n=max(powers[:first-1],default=0) if first else None,
            null_rejection_at_first_n=null[first-1] if first else None,
            scenarios=[dict(n=n,rejection_probability=powers[n-1],same_activity_symmetric_null_rejection=null[n-1]) for n in GRID]))
    # Mixed test: preserve five initial-score strata and fixed allocation counts.
    for n in GRID:
        for allocation in ['fixed_52','approximately_fixed_fraction']:
            transformed=52 if allocation=='fixed_52' else 4*round(n*(52/125)/4)
            for repair in [.25,.5]:
                g=rng(f'mixed-score-{n}-{allocation}-{repair}')
                pos=np.zeros(DRAWS,dtype=int); neg=pos.copy(); null_pos=pos.copy(); null_neg=pos.copy()
                expected_change=0
                for name,totals in strata.items():
                    count=n-transformed if name==unchanged else transformed//4
                    positive,negative=score_probabilities(totals,repair,.01)
                    counts=g.multinomial(count,[positive,negative,1-positive-negative],size=DRAWS)
                    pos+=counts[:,0];neg+=counts[:,1]
                    activity=positive+negative
                    counts=g.multinomial(count,[activity/2,activity/2,1-activity],size=DRAWS)
                    null_pos+=counts[:,0];null_neg+=counts[:,1]
                    expected_change+=count*(positive-negative)/n
                result['mixed_wilcoxon'].append(dict(n=n,allocation=allocation,transformed=transformed,
                    improve_if_eligible=repair,harm_probability=.01,expected_mean_change=expected_change,
                    rejection_probability=rate(signed_count_p(pos,neg)<.05),
                    same_activity_symmetric_null=rate(signed_count_p(null_pos,null_neg)<.05)))
    # Four sequential batches are not independent pipeline replications.
    # Null calibration under a latent Gaussian shared-batch shock, not an estimated ICC.
    for n in [100,125,250,500]:
        sizes=[n//4]*4
        for i in range(n%4): sizes[-1-i]+=1
        batch=np.repeat(np.arange(4),sizes)
        for rho in [0,.05]:
            g=rng(f'dependence-{n}-{rho}'); rejected=[]
            for _ in range(DRAWS//1000):
                z=np.sqrt(1-rho)*g.normal(size=(1000,n))
                if rho: z+=np.sqrt(rho)*g.normal(size=(1000,4))[:,batch]
                d=np.clip(np.rint(2*z),-8,8)
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore', RuntimeWarning)
                    p=wilcoxon(d,axis=1,zero_method='pratt',alternative='two-sided',
                        correction=False,method='asymptotic').pvalue
                assert np.all(np.isfinite(p))
                rejected.extend(p<.05)
            result['dependence'].append(dict(n=n,batch_sizes=sizes,latent_batch_correlation=rho,
                zero_shift_rejection_probability=rate(rejected)))
    assert before == {p.relative_to(ROOT).as_posix():digest(p) for p in sources}
    result.update(source_files_unchanged=True,model_api_calls=0,network_calls=0,
        final_sample_size_changed=False,final_analysis_changed=False)
    out.mkdir(parents=True,exist_ok=True)
    with (out/'results.json').open('x',encoding='utf-8') as f:
        json.dump(result,f,ensure_ascii=False,indent=2,allow_nan=False); f.write('\n')
    print(json.dumps(dict(output=str(out/'results.json'),iid_minima=[(x['improve_if_eligible'],x['first_n_at_80']) for x in result['iid_wilcoxon']],sources_unchanged=True)))

if __name__=='__main__':
    main()
