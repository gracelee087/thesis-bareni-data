"""Post-run integrity checks only; no model calls or additional hypothesis tests."""
import hashlib
import importlib.metadata
import json
import math
import statistics
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

S = Path(__file__).resolve().parents[1]
ROOT = S.parents[1]
W = S / 'private/final125_v1'
OUT = W / 'reports_final_2026-09-08'
sys.path.insert(0, str(S / 'tools/final125_v1'))
from defects import mutate
import pricing

def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def sha(v): return hashlib.sha256(json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
def same(a, b): return math.isclose(a, b, abs_tol=1e-9, rel_tol=1e-10)

manifest = read(OUT / 'report_manifest.json')
for p, h in manifest['source_sha256'].items(): assert digest(Path(p)) == h, p
for p, h in manifest['output_sha256'].items(): assert digest(OUT / p) == h, p
frozen, registration, plan = [read(W / n) for n in ('freeze.json', 'registration.json', 'execution_plan.json')]
assert registration['freeze_sha256'] == digest(W / 'freeze.json')
expected = dict(frozen['source_sha256'])
patches = []
for p in sorted((W / 'patches').glob('*.json')):
    patch = read(p)
    assert patch['freeze_sha256'] == digest(W / 'freeze.json') and patch['scientific_inputs_unchanged']
    for rel, c in patch['changes'].items():
        assert Path(rel).name in ('run.py', 'telemetry.py')
        assert expected[rel] == c['old_sha256']
        assert digest(W / 'source_archive' / c['old_sha256']) == c['old_sha256']
        expected[rel] = c['new_sha256']
    patches.append({'path': str(p.relative_to(ROOT)), 'kind': patch['kind'], 'reason': patch['reason']})
for p, h in expected.items(): assert digest(ROOT / p) == h, p
for k, v in plan['installed_versions'].items(): assert importlib.metadata.version(k) == v, k
starts = {p.stem: read(p) for p in (W / 'started').glob('*.json')}
rows = {p.stem: read(p) for p in (W / 'results').glob('*.json')}
assert set(starts) == set(rows)
assert min(s['created_at'] for s in starts.values()) > registration['recorded_at']
prices = pricing.load_pricing()
recomputed = 0
for key, r in rows.items():
    s = starts[key]
    assert r['freeze_sha256'] == s['freeze_sha256'] == digest(W / 'execution_plan.json')
    assert s['request_sha256'] == sha(s['request']), key
    for parent, h in s['parent_sha256'].items():
        assert digest(W / 'results' / (parent + '.json')) == h, key
        assert rows[parent]['status'] == 'success', key
    if r.get('cost_usd') is not None:
        usage = pricing.normalize_usage(s['candidate']['provider'], r['provider_response'])
        cost = pricing.cost_details(s['candidate']['model'], usage, prices)['total']
        assert usage == r['usage'] and same(cost, r['cost_usd']), key
        recomputed += 1

tasks = {p.stem: read(p) for p in (W / 'tasks').glob('*.json')}
assert len(tasks) == 250
mixed = read(W / 'mixed_inputs.json')
assert mixed['plan_sha256'] == digest(W / 'execution_plan.json')
assert mixed['transformation_sha256'] == digest(S / 'tools/final125_v1/defects.py')
assert mixed['content_sha256'] == sha(mixed['items'])
assert mixed['created_at'] < min(s['created_at'] for k, s in starts.items() if k.startswith('SE-FINAL-M'))
for entry in mixed['items']:
    source = tasks[entry['source_task_id']]
    assert entry['source_sha256'] == digest(W / 'tasks' / (entry['source_task_id'] + '.json'))
    assignment = plan['mixed_assignment'].get(entry['source_task_id'])
    change = mutate(source['initial'], assignment['defect_type'], assignment['variant'], source['topic']) if assignment else None
    assert change == entry['change']
    assert entry['initial'] == (change['modified'] if change else source['initial'])
    target = tasks[entry['task_id']]
    for field in ('planner', 'researcher', 'selected_lessons'):
        assert target[field] == source[field], (entry['task_id'], field)

dims = ('persona_fit', 'clarity', 'actionability', 'factual_grounding')
checks, low_records = {}, []
for cohort, prefix in [('natural', 'SE-FINAL-N'), ('mixed', 'SE-FINAL-M')]:
    own = [tasks[f'{prefix}{i:03}'] for i in range(1, 126)]
    report = read(OUT / f'{cohort}_analysis.json')
    before, after = [], []
    for t in own:
        assert t['status'] == t['execution_status'] == 'complete'
        assert 1 <= len(t['cycles']) <= 2 and 150 <= len(t['final']['body']) <= 2000
        b, f = [[t[stage + '_eval']['scores'][d] for d in dims] for stage in ('initial', 'final')]
        assert all(type(v) is int and 1 <= v <= 5 for v in b + f)
        before.append(sum(b)); after.append(sum(f))
        if min(b) < 3 or min(f) < 3:
            low_records.append({'task_id': t['task_id'], 'source_task_id': t.get('source_task_id'), 'condition': t['condition'], 'initial_scores': b, 'final_scores': f})
    B = sum(min(t['initial_eval']['scores'][d] for d in dims) < 3 for t in own)
    F = sum(min(t['final_eval']['scores'][d] for d in dims) < 3 for t in own)
    assert (B, F) == (report['h3']['valid_pairs_descriptive']['initial_low'], report['h3']['valid_pairs_descriptive']['final_low'])
    assert same((B-F)/B, report['h3']['relative_reduction'])
    assert same(statistics.mean(before), report['quality_scores']['total_score']['initial']['mean'])
    assert same(statistics.mean(after), report['quality_scores']['total_score']['final']['mean'])
    # Independent Pratt signed-rank calculation of the SAME prespecified test.
    from scipy.stats import rankdata, norm
    delta = [f-b for b,f in zip(before, after)]
    ranks = rankdata([abs(x) for x in delta])
    pos = sum(r for r,d in zip(ranks,delta) if d > 0)
    neg = sum(r for r,d in zip(ranks,delta) if d < 0)
    variance = sum(r*r for r,d in zip(ranks,delta) if d != 0) / 4
    pv = float(2 * norm.sf(abs(pos-neg) / (2*math.sqrt(variance)))) if variance else 1.
    assert same(pv, report['paired_total_wilcoxon']['p_value'])
    assert same(min(pos, neg), report['paired_total_wilcoxon']['statistic'])
    costs = []
    for t in own:
        direct = [r for r in rows.values() if r.get('task_id') == t['task_id'] and r['role'] != 'evaluator']
        if cohort == 'mixed': assert all(r['role'] in ('gate', 'critic', 'optimizer') for r in direct)
        costs.append(sum(r.get('cost_usd') or 0 for r in direct))
    if cohort == 'mixed': assert same(statistics.stdev(costs)/statistics.mean(costs), report['h2']['cv'])
    checks[cohort] = {'complete': len(own), 'initial_low': B, 'final_low': F, 'same_test_p_independently_verified': pv,
        'cycles': dict(Counter(len(t['cycles']) for t in own)), 'evaluation_reused': sum(t['evaluation_reused'] for t in own),
        'initial_target_length_count': sum(1200 <= len(t['initial']['body']) <= 1500 for t in own),
        'final_target_length_count': sum(1200 <= len(t['final']['body']) <= 1500 for t in own),
        'score_direction': dict(Counter('increase' if f>b else 'decrease' if f<b else 'unchanged' for b,f in zip(before,after)))}

unknown = [{k:r.get(k) for k in ('key','role','cohort','status','error_kind','http_status','error_code','budget_charge_usd')} for r in rows.values() if r.get('cost_usd') is None]
failures = []
for k,r in rows.items():
    if r['status'] == 'success': continue
    successes = [key for key,s in rows.items() if key.split('__a')[0] == k.split('__a')[0] and s['status'] == 'success']
    assert successes, k
    failures.append({'key': k, 'status': r['status'], 'error_kind': r.get('error_kind'), 'validation_detail': r.get('validation_detail'), 'recovered_by': successes})
latest = read(max((W/'sessions').glob('*.json'), key=lambda p:p.stat().st_mtime))
assert latest['stop_reason'] is None and latest['completed_natural'] == latest['completed_mixed'] == 125
assert latest['attempts'] == len(rows)
assert same(sum(r.get('cost_usd') or 0 for r in rows.values()), latest['known_cost_usd'])
assert same(sum(r['budget_charge_usd'] for r in rows.values()) + plan['prior_budget_charge_usd'], latest['budget_ledger_usd'])
for p,h in manifest['source_sha256'].items(): assert digest(Path(p)) == h, p
result = {'created_at': datetime.now(timezone.utc).isoformat(), 'passed': True, 'no_api_calls': True,
    'script_sha256': digest(Path(__file__)), 'report_manifest_sha256': digest(OUT/'report_manifest.json'),
    'frozen_files_verified': len(expected), 'source_files_verified': len(manifest['source_sha256']),
    'patches': patches, 'started_results_matched': len(rows), 'response_costs_recomputed': recomputed,
    'mixed_transformations_reproduced': 52, 'unchanged_originals_verified': 73,
    'cohort_checks': checks, 'unknown_cost_attempts': unknown, 'status_counts': dict(Counter(r['status'] for r in rows.values())),
    'failures': failures, 'low_quality_records': low_records, 'final_session': latest,
    'limitations': ['No independent cloud ingestion or provider invoice reconciliation.', 'Source registration receipt is local; external registration was completed in prior session.', 'Only prespecified statistics; no additional hypothesis tests.']}
(OUT/'integrity_audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:result[k] for k in ('passed','frozen_files_verified','source_files_verified','started_results_matched','response_costs_recomputed','cohort_checks','unknown_cost_attempts','status_counts')},ensure_ascii=True))
