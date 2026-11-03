"""Prepare a prospective, outcome-independent workload; never call providers."""
from __future__ import annotations
import copy
import hashlib
import importlib.metadata
import json
import random
import re
import unicodedata
from pathlib import Path
import pricing

S = Path(__file__).resolve().parents[2]
ROOT = S.parents[1]
W = S / 'private/final125_v1'
SEED = 20260907
TYPES = ['fabricated_evidence', 'wrong_audience', 'no_actionable_step', 'incoherent']


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def put(path, value):
    path = Path(path)
    if path.exists():
        if read(path) != value:
            raise RuntimeError('Existing preparation differs; preserve/version it: ' + str(path))
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as out:
        json.dump(value, out, ensure_ascii=False, indent=2, allow_nan=False)
        out.write('\n')


def norm(text):
    return ' '.join(unicodedata.normalize('NFKC', text).casefold().split()).strip(' .')


def inventory():
    bank = ROOT / '주제.md'
    unique = {}
    for n, line in enumerate(bank.read_text(encoding='utf-8').splitlines(), 1):
        text = line.strip()
        if text and not text.startswith('#'):
            unique.setdefault(norm(text), dict(source_line=n, abstract_topic=text))
    used = {key: set() for key in unique}
    scanned, invalid = [], []
    # Old topic inventories explicitly distinguish used/reserved entries from unused ones.
    old = read(S / 'private/pilot125_v1/topic_inventory.json')
    oldbank = read(ROOT / old['bank_path'])
    def collect_bank(value):
        if isinstance(value, dict):
            if value.get('topic_id') in old['used'] and isinstance(value.get('abstract_topic'), str):
                key = norm(value['abstract_topic'])
                if key in used:
                    used[key].update(old['used'][value['topic_id']])
            for v in value.values(): collect_bank(v)
        elif isinstance(value, list):
            for v in value: collect_bank(v)
    collect_bank(oldbank)
    def collect(value, path):
        if isinstance(value, dict):
            for k, v in value.items():
                if isinstance(v, str):
                    if k in ('abstract_topic', 'topic', 'title') and norm(v) in used:
                        used[norm(v)].add(path)
                    # Started-but-unfinished calls count as exposure, too.
                    for m in re.finditer(r'Owner-specified abstract topic:\*\*\s*([^\n]+)', v):
                        if norm(m.group(1)) in used: used[norm(m.group(1))].add(path)
                elif isinstance(v, (dict, list)): collect(v, path)
        elif isinstance(value, list):
            for v in value: collect(v, path)
    for directory in (ROOT / 'data', ROOT / 'studies', ROOT / 'study_b'):
        if not directory.exists(): continue
        for path in sorted(directory.rglob('*.json')):
            if W in path.parents or any(p in ('topic_bank', 'topic_banks', '__pycache__') for p in path.parts):
                continue
            if path.name in ('topic_inventory.json',) or 'topic_bank' in path.name:
                continue  # The complete bank alone does not mean every topic was used.
            rel = path.relative_to(ROOT).as_posix()
            try: value = read(path)
            except (ValueError, UnicodeError):
                invalid.append(rel)
                continue
            collect(value, rel)
            scanned.append(dict(path=rel, sha256=digest(path)))
    if invalid:
        raise RuntimeError('Unreadable historical JSON requires audit: ' + repr(invalid[:8]))
    free = [entry for key, entry in unique.items() if not used[key]]
    if len(free) < 125:
        raise RuntimeError(f'Only {len(free)} unused normalized topics remain')
    return dict(bank_path=bank.relative_to(ROOT).as_posix(), bank_sha256=digest(bank),
                unique_topics=len(unique), used_or_reserved=sum(bool(v) for v in used.values()),
                eligible=len(free), used={k: sorted(v) for k, v in used.items() if v},
                eligible_topics=free, scanned_files=scanned,
                policy='NFKC/casefold/whitespace exact topic equality, historical allocation counts as exposure; semantic independence is not guaranteed. No outcome score is used.')


def prepare():
    if (W / 'execution_plan.json').exists():
        return read(W / 'execution_plan.json')
    inv = inventory()
    selected = random.Random(SEED).sample(inv['eligible_topics'], 125)
    put(W / 'topic_inventory.json', inv)
    put(W / 'selected_topics.json', dict(seed=SEED, source_sha256=inv['bank_sha256'], items=selected))
    base = read(S / 'private/long125_v2/execution_plan.json')
    tasks = []
    for index, (oldtask, entry) in enumerate(zip(base['tasks'], selected), 1):
        t = copy.deepcopy(oldtask)
        oldtopic = oldtask['topic']['abstract_topic']
        def change(v):
            if isinstance(v, str): return v.replace(oldtopic, entry['abstract_topic'])
            if isinstance(v, list): return [change(x) for x in v]
            if isinstance(v, dict): return {k: change(x) for k, x in v.items()}
            return v
        t = change(t)
        t.update(task_id=f'SE-FINAL-N{index:03}', index=index,
                 topic=dict(entry, topic_id=f'FINAL-T{index:03}'), condition='natural')
        t.pop('paired_short_task_id', None)
        tasks.append(t)
    rng = random.Random(SEED)
    corrupt = rng.sample([t['task_id'] for t in tasks], 52)
    rng.shuffle(corrupt)
    assignment = {key: dict(defect_type=TYPES[i // 13], variant=i % 13) for i, key in enumerate(corrupt)}
    mixed_order = [t['task_id'] for t in tasks]
    random.Random(SEED + 1).shuffle(mixed_order)
    dependencies = ['langgraph', 'langgraph-checkpoint', 'langfuse', 'openai', 'anthropic', 'google-genai', 'pydantic', 'python-dotenv', 'numpy', 'scipy']
    versions = {name: importlib.metadata.version(name) for name in dependencies}
    plan = dict(status='prepared_not_preregistered', seed=SEED, tasks=tasks,
                mixed_assignment=assignment, mixed_order=mixed_order,
                templates=base['templates'], batch_sizes=[31,31,31,32], workers=2,
                cap_usd=49.99, prior_budget_charge_usd=0.0, cap_scope='New final natural125 and mixed125 combined; historical pilot charges excluded and preserved separately.',
                request_timeout_seconds=180, max_calls=5000, max_refinements=2,
                schema_retry_limit=12, transport_retry_limit=7, rate_limit_retry_limit=24,
                max_register_entries=12, max_proposals=3, representative_failures_max=5,
                minimum_provider_interval_seconds=2.0,
                identical_text_evaluation_reuse=True, length=base['length'],
                sdk_versions=base['sdk_versions'], installed_versions=versions,
                persona=(S.parent/'study_d/config/persona_experiment.md').read_text(encoding='utf-8'),
                topic_inventory_sha256=digest(W/'topic_inventory.json'),
                source_bank_sha256=digest(ROOT/'주제.md'),
                prototype_plan_sha256=digest(S/'private/long125_v2/execution_plan.json'),
                scientific_policy='Natural: new unused normalized topics, real Planner->Researcher->Writer->Gate->Critic->Optimizer->Gate, force first refinement, maximum two. Independent initial/final measurement after production, never feedback. Batch Curator with initially empty memory. Mixed: same Writer initial drafts, deterministic52 faults and73 unchanged; saved upstream/lessons, no new memory. No quality-driven retries, replacement, or outcome-based topic selection. Technical failures are preserved, patched/resumed within fixed budgets; uncompleted/missing are reported honestly.')
    plan = pricing.apply_to_plan(plan, pricing.load_pricing())
    put(W/'execution_plan.json', plan)
    return plan


if __name__ == '__main__':
    plan = prepare()
    inv = read(W/'topic_inventory.json')
    print(json.dumps(dict(prepared=len(plan['tasks']), eligible=inv['eligible'], excluded=inv['used_or_reserved'],
                          unique_topics=inv['unique_topics'], paid_calls=0, status=plan['status'])))
