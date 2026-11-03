"""Derive separate Proposal-only supplements for the two completed Study E pilots.
Never rewrites pilot artifacts. No API calls. Not a prospective final result.
"""
import argparse
import csv
import hashlib
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('proposal_pilot_analysis', HERE / 'analysis.py')
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)
DEFAULT_PRIVATE = HERE.parents[1] / 'private'


def build_pilot_supplement(private_dir, output_dir):
    private_dir, output_dir = Path(private_dir).resolve(), Path(output_dir).resolve()
    for name in ('long125_v2', 'mixed125_v1'):
        original = private_dir / name
        if output_dir == original or original in output_dir.parents:
            raise ValueError('Supplement must be outside either preserved pilot directory')
    reads, results = {}, {}
    def read(path):
        data = path.read_bytes()
        reads[str(path)] = hashlib.sha256(data).hexdigest()
        return json.loads(data.decode('utf-8-sig'))
    for condition, name in (('natural', 'long125_v2'), ('mixed', 'mixed125_v1')):
        folder = private_dir / name
        plan = read(folder / 'execution_plan.json')
        planned = plan['tasks']
        ids = [x['task_id'] for x in planned]
        if len(ids) != 125 or len(set(ids)) != 125:
            raise ValueError('Pilot plan must contain 125 unique tasks')
        by_id = {x['task_id']: x for x in planned}
        rows = []
        for item in planned:
            path = folder / 'tasks' / (item['task_id'] + '.json')
            if not path.exists():
                continue
            row = read(path)
            if row.get('task_id') != item['task_id']:
                raise ValueError('Pilot task identity mismatch')
            if row.get('batch_id', item['batch_id']) != item['batch_id']:
                raise ValueError('Pilot task batch mismatch')
            row.setdefault('batch_id', item['batch_id'])
            row.setdefault('condition', 'natural' if condition == 'natural' else row.get('defect_type', item.get('defect_type', 'unchanged')))
            # Preserve actual status/evaluations/selected output: no completion imputation.
            rows.append(row)
        starts = {p.stem: read(p) for p in sorted((folder / 'started').glob('*.json'))}
        outcomes = {p.stem: read(p) for p in sorted((folder / 'results').glob('*.json'))}
        if set(outcomes) - set(starts):
            raise ValueError('Pilot result without immutable start')
        calls = []
        for key, start in starts.items():
            if start.get('key') != key:
                raise ValueError('Pilot start key mismatch')
            row = dict(outcomes[key]) if key in outcomes else dict(key=key, role=start['role'], status='pending_or_interrupted_unknown', cost_usd=None,
                unknown_cost_reservation_usd=start['reserved_usd'], budget_charge_usd=start['reserved_usd'])
            if row.get('key') != key or row.get('role') != start.get('role'):
                raise ValueError('Pilot attempt key or role mismatch')
            if row.get('freeze_sha256') is not None and row['freeze_sha256'] != start.get('freeze_sha256'):
                raise ValueError('Pilot attempt freeze mismatch')
            row.setdefault('created_at', start.get('created_at'))
            matches = [task_id for task_id in ids if key.startswith(task_id + '_')]
            if len(matches) == 1:
                row['task_id'] = matches[0]
                row['batch_id'] = by_id[matches[0]]['batch_id']
            elif row['role'] == 'memory' and condition == 'natural':
                import re
                match = re.fullmatch(r'batch([1-4])_curator__a\d+', key)
                if not match:
                    raise ValueError('Unknown pilot memory key')
                row['batch_id'] = int(match.group(1))
            else:
                raise ValueError('Pilot attempt outside planned cohort: ' + key)
            calls.append(row)
        result = a.analyze(rows, calls, expected_task_ids=ids, condition=condition,
                           expected_batch_by_task={x['task_id']: x['batch_id'] for x in planned})
        result['report_status'] = 'retrospective_pilot_supplement'
        result['provenance'] = dict(source_run=name, attempted_calls=len(calls),
            unchanged_original_records=True, prospective_final_result=False,
            note='New Proposal-only offline derivation from preserved pilot records. No newly generated text or evaluation. Original report conventions are not overwritten; production wall-clock lacks historic completion timestamps and remains undefined.')
        results[condition] = result
    for path, digest in reads.items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest() != digest:
            raise RuntimeError('Source changed during supplement: ' + path)
    output_dir.mkdir(parents=True, exist_ok=True)
    def write_json(name, value):
        (output_dir / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    def write_csv(name, rows):
        with (output_dir / name).open('w', encoding='utf-8-sig', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader(); writer.writerows(rows)
    texts, latency, scores = [], [], []
    for condition, result in results.items():
        write_json(condition + '_proposal_analysis.json', result)
        for item in result['items']:
            for stage in ('initial', 'final'):
                texts.append(dict(condition=condition, task_id=item['task_id'], stage=stage, **item[stage + '_text_metrics']))
                scores.append(dict(condition=condition, task_id=item['task_id'], stage=stage,
                                   total_score=item[stage + '_total'], **(item[stage + '_scores'] or {k: None for k in a.DIMENSIONS})))
        for role, stats in result['latency']['by_role_attempt'].items():
            latency.append(dict(condition=condition, scope='role_attempt', role=role, **stats))
        for scope in ('task_production_call_sum', 'task_production_wall_clock'):
            latency.append(dict(condition=condition, scope=scope, role='all_direct_production', **result['latency'][scope]))
    write_csv('text_metrics_500.csv', texts)
    write_csv('quality_scores_500.csv', scores)
    write_csv('latency_descriptive.csv', latency)
    (output_dir / 'README.md').write_text('''# Preserved-pilot Proposal-only supplement

Retrospective, API-free computation from long125_v2 and mixed125_v1. These are not
results of the newly planned final125 experiment. Original pilot files are untouched.
The two runs share source tasks. Do not pool them as 250 independent observations.

H1/H2/H3 point criteria, four score dimensions, English body-only Flesch ease/grade,
word count, type-token lexical diversity, descriptive costs and latency, and paired
total-score two-sided Wilcoxon are computed by the current Proposal-only analysis.
The four low/pass transition counts only reconcile B-F; no additional tests or Gate
subset tables are produced. The Wilcoxon result uses Pratt zeros and asymptotic
inference without continuity correction; original reports remain separate records.

Unknown production usage prevents actual H2 CV. Known costs and unknown reservations
stay separate. Historic task completion timestamps were not stored, so task wall-clock
is undefined. Role latency and per-task direct production call sums use observed
latency_ms, including failed attempts; unknown timings are not zeros. They exclude
batch Curator and evaluator from task production sums, with role data shown separately.
Text statistics are English heuristics and do not validate factual truth or AI scores.
JSON analysis_settings contains the exact formulas. Missing values stay missing.
''', encoding='utf-8')
    manifest = dict(created_at=datetime.now(timezone.utc).isoformat(), no_api_calls=True,
                    original_records_unchanged=True, source_sha256=reads,
                    implementation_sha256={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (HERE/'analysis.py', Path(__file__).resolve())},
                    output_sha256={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in output_dir.iterdir() if p.is_file() and p.name != 'manifest.json'})
    write_json('manifest.json', manifest)
    return {condition: dict(h1=result['h1']['rate'], h2_cv=result['h2']['cv'], h3=result['h3']['relative_reduction'],
                            wilcoxon_p=result['paired_total_wilcoxon']['p_value'], calls=result['provenance']['attempted_calls']) for condition, result in results.items()}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--private', type=Path, default=DEFAULT_PRIVATE)
    parser.add_argument('--output', type=Path, default=DEFAULT_PRIVATE/'proposal_only_pilot_analysis_v1')
    args = parser.parse_args()
    print(json.dumps(build_pilot_supplement(args.private, args.output), ensure_ascii=False))
