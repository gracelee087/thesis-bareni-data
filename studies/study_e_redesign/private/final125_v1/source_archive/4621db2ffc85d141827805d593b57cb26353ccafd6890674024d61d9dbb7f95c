"""Read-only raw-record reporting for final Study E. No runtime/provider imports.

Usage: python report.py --workspace <private/final125_v1> --output <reports>
API: build_reports(workspace, output_dir) -> JSON-serializable receipt.
"""
from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import importlib.util
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("study_e_final_report_analysis", HERE / "analysis.py")
_analysis = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_analysis)
analyze = _analysis.analyze
DEFAULT_WORKSPACE = HERE.parents[1] / "private" / "final125_v1"
ROLES = ("planner", "researcher", "writer", "gate", "critic", "optimizer", "memory", "evaluator")
STAGES = ("Planner", "Researcher", "Writer", "Gate_initial", "Critic", "Optimizer", "Gate_final", "initial_eval", "final_eval")
STAGE_RE = re.compile(r"^(planner|researcher|writer|gate[012]|critic[12]|optimizer[12]|eval_initial|eval_final)$")
KEY_RE = re.compile(r"^(.*)__a(\d+)$")


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _json(path, reads):
    data = path.read_bytes()
    value = json.loads(data.decode("utf-8-sig"))
    reads[str(path)] = _sha(data)
    return value


def _write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def _write_csv(path, rows, fields=None):
    fields = fields or list(rows[0])
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)


def _planned_cohorts(plan, mixed):
    natural = copy.deepcopy(plan["tasks"])
    if len(natural) != 125 or len({r["task_id"] for r in natural}) != 125:
        raise ValueError("Final protocol requires exactly 125 unique natural task IDs")
    natural_by_id = {t["task_id"]: t for t in natural}
    for index, task in enumerate(natural, 1):
        if task.get("condition", "natural") != "natural":
            raise ValueError("Natural plan contains another condition")
        task["condition"] = "natural"
        if task.get("batch_id") != 1 + (index > 31) + (index > 62) + (index > 93):
            raise ValueError("Natural batch allocation is not 31/31/31/32 in planned order")
    order = plan["mixed_order"]
    if len(order) != 125 or set(order) != set(natural_by_id) or len(set(order)) != 125:
        raise ValueError("Mixed planned order must use each natural task exactly once")
    assignment = plan["mixed_assignment"]
    expected_types = {"fabricated_evidence", "wrong_audience", "no_actionable_step", "incoherent"}
    if len(assignment) != 52 or not set(assignment) <= set(natural_by_id):
        raise ValueError("Exactly 52 planned natural IDs must have a defect assignment")
    counts = Counter(x.get("defect_type") for x in assignment.values())
    if set(counts) != expected_types or any(v != 13 for v in counts.values()):
        raise ValueError("Mixed plan must retain four defect types, 13 each")
    planned_mixed = []
    for index, source_id in enumerate(order, 1):
        planned_mixed.append(dict(
            task_id=f"SE-FINAL-M{index:03}", index=index,
            batch_id=1 + (index > 31) + (index > 62) + (index > 93),
            source_task_id=source_id, source_batch_id=natural_by_id[source_id]["batch_id"],
            condition=assignment.get(source_id, {}).get("defect_type", "unchanged"),
        ))
    if mixed is not None:
        entries = mixed.get("items")
        if not isinstance(entries, list) or len(entries) != 125:
            raise ValueError("Mixed input manifest must have 125 entries")
        indexed = {x["task_id"]: x for x in entries}
        if len(indexed) != 125 or set(indexed) != {x["task_id"] for x in planned_mixed}:
            raise ValueError("Mixed input manifest task IDs differ from fixed plan")
        for task in planned_mixed:
            actual = indexed[task["task_id"]]
            for key in ("source_task_id", "condition", "batch_id", "source_batch_id"):
                if actual.get(key) != task[key]:
                    raise ValueError("Mixed manifest differs from plan: " + task["task_id"] + "/" + key)
            task.update(copy.deepcopy(actual))
    return {"natural": natural, "mixed": planned_mixed}


def _classify_key(key, expected):
    match = KEY_RE.fullmatch(key)
    if not match:
        return None
    logical = match.group(1)
    for task_id, task in expected.items():
        if logical.startswith(task_id + "_"):
            stage = logical[len(task_id) + 1:]
            if not STAGE_RE.fullmatch(stage):
                raise ValueError("Unknown stage under planned task: " + key)
            role = "evaluator" if stage.startswith("eval_") else re.sub(r"[012]$", "", stage)
            return dict(task_id=task_id, batch_id=task["batch_id"], cohort=task["cohort"], role=role, stage=stage)
    batch = re.fullmatch(r"batch_?([1-4])_(?:curator|memory)", logical)
    if batch:
        return dict(task_id=None, batch_id=int(batch.group(1)), cohort="natural", role="memory", stage="memory")
    return None


def _attempts(workspace, expected, reads):
    starts, results = {}, {}
    excluded = []
    for dirname, target in (("started", starts), ("results", results)):
        for path in sorted((workspace / dirname).glob("*.json")):
            classification = _classify_key(path.stem, expected)
            if classification is None:
                excluded.append(str(path.relative_to(workspace)))
                continue
            row = _json(path, reads)
            if row.get("key") != path.stem:
                raise ValueError("Attempt filename/key mismatch: " + str(path))
            metadata = row.get("metadata") or {}
            for key in ("task_id", "batch_id", "cohort", "role"):
                for container in (row, metadata):
                    value = container.get(key)
                    if value is not None and value != classification[key]:
                        raise ValueError("Attempt key/metadata disagreement: " + path.stem + "/" + key)
            if row.get("role") != classification["role"]:
                raise ValueError("Attempt role missing or inconsistent: " + path.stem)
            if classification["cohort"] == "mixed" and classification["role"] in {"planner", "researcher", "writer", "memory"}:
                raise ValueError("Unexpected new upstream/Curator call in mixed cohort")
            target[path.stem] = (row, classification)
    if set(results) - set(starts):
        raise ValueError("Result without matching immutable start: " + ", ".join(sorted(set(results) - set(starts))))
    attempts = {"natural": [], "mixed": []}
    unresolved = []
    for key, (start, classification) in sorted(starts.items()):
        if key in results:
            row = copy.deepcopy(results[key][0])
            if row.get("freeze_sha256") is not None and start.get("freeze_sha256") != row["freeze_sha256"]:
                raise ValueError("Attempt start/result freeze mismatch: " + key)
        else:
            reserved = start.get("reserved_usd")
            if not isinstance(reserved, (int, float)) or isinstance(reserved, bool) or reserved < 0:
                raise ValueError("Unresolved start lacks a nonnegative reservation: " + key)
            row = dict(key=key, role=classification["role"], status="pending_or_interrupted_unknown",
                       output=None, cost_usd=None, budget_charge_usd=reserved,
                       unknown_cost_reservation_usd=reserved, report_synthesized=True)
            unresolved.append(key)
        row.setdefault("created_at", start.get("created_at"))
        row.update(classification)
        attempts[classification["cohort"]].append(row)
    return attempts, unresolved, excluded


def _successful_output(attempts, task_id, stage, explicit_key=None):
    matches = [x for x in attempts if x["task_id"] == task_id and x["stage"] == stage and x["status"] == "success"]
    if explicit_key is not None:
        selected = [x for x in matches if x["key"] == explicit_key]
        if len(selected) != 1:
            raise ValueError("Task references missing/non-successful stage: " + explicit_key)
        return selected[0]
    if len(matches) > 1:
        raise ValueError("Multiple successful calls without task selection: " + task_id + "/" + stage)
    return matches[0] if matches else None


def _task_rows(workspace, planned, attempts, reads):
    rows, origins = [], {}
    for task in planned:
        task_id = task["task_id"]
        path = workspace / "tasks" / (task_id + ".json")
        source = "tasks"
        if not path.exists():
            path = workspace / "production" / (task_id + ".json")
            source = "production"
        if path.exists():
            row = copy.deepcopy(_json(path, reads))
            if row.get("task_id") != task_id:
                raise ValueError("Task filename/ID mismatch: " + str(path))
            for key in ("batch_id", "condition", "source_task_id"):
                if row.get(key) is not None and row[key] != task.get(key):
                    raise ValueError("Task record differs from plan: " + task_id + "/" + key)
        else:
            source = "planned_only"
            row = dict(task_id=task_id, execution_status="not_recorded", status="not_recorded")
            # Input availability is not successful processing or outcome measurement.
            if "initial" in task:
                row["initial"] = copy.deepcopy(task["initial"])
        origins[task_id] = source
        row.update(batch_id=task["batch_id"], condition=task["condition"], source_task_id=task.get("source_task_id"))
        if row.get("execution_status", row.get("status")) == "complete":
            for field, key_field, expected_prefix in (("final", "final_key", "optimizer"), ("final_gate", "final_gate_key", "gate")):
                key = row.get(key_field)
                if not isinstance(key, str):
                    raise ValueError("Complete production record lacks " + key_field + ": " + task_id)
                classification = _classify_key(key, {task_id: dict(task, cohort="natural" if task["condition"] == "natural" else "mixed")})
                if classification is None or not classification["stage"].startswith(expected_prefix) or classification["stage"] == "gate0":
                    raise ValueError("Invalid final production provenance: " + key)
                found = _successful_output(attempts, task_id, classification["stage"], key)
                if row.get(field) != found["output"]:
                    raise ValueError("Final production artifact differs from selected successful result: " + task_id + "/" + field)
            initial_gate = _successful_output(attempts, task_id, "gate0")
            if initial_gate is None or row.get("initial_gate") != initial_gate["output"]:
                raise ValueError("Initial Gate artifact lacks matching successful result: " + task_id)
        if "initial" not in row and task["condition"] == "natural":
            writer = _successful_output(attempts, task_id, "writer", row.get("writer_key"))
            if writer:
                row["initial"] = writer["output"]
        if task["condition"] == "natural" and row.get("initial") is not None:
            writer = _successful_output(attempts, task_id, "writer", row.get("writer_key"))
            if writer is None or row["initial"] != writer["output"]:
                raise ValueError("Natural initial draft lacks Writer result provenance: " + task_id)
        if task["condition"] != "natural" and row.get("initial") is not None:
            if "initial" not in task or row["initial"] != task["initial"]:
                raise ValueError("Mixed initial draft differs from frozen input manifest: " + task_id)
        # A checkpoint may predate successful evaluation calls. Recover only actual
        # successful outputs; never infer a measurement from a future cache rule.
        keys = row.get("evaluation_keys", [])
        for stage, index in (("initial", 0), ("final", 1)):
            explicit = keys[index] if len(keys) > index else row.get(stage + "_eval_key")
            call_stage = "eval_" + stage
            if stage == "final" and row.get("evaluation_reused") is True:
                if row.get("initial") != row.get("final"):
                    # Production objects may have extra metadata; compare text fields.
                    if not all(row.get("initial", {}).get(k) == row.get("final", {}).get(k) for k in ("title", "body")):
                        raise ValueError("Evaluation reused for changed text: " + task_id)
                if explicit is not None and keys and explicit != keys[0]:
                    raise ValueError("Reused final evaluation key differs from initial")
                call_stage = "eval_initial"
            found = _successful_output(attempts, task_id, call_stage, explicit)
            if found:
                field = stage + "_eval"
                if row.get(field) is not None and row[field] != found["output"]:
                    raise ValueError("Embedded evaluation differs from immutable result: " + task_id + "/" + field)
                row[field] = found["output"]
            elif row.get(stage + "_eval") is not None:
                raise ValueError("Embedded evaluation has no successful API provenance: " + task_id)
        # Do not declare production complete from a successful final Gate alone:
        # the explicit production/checkpoint status remains authoritative for H1.
        rows.append(row)
    return rows, origins


def _stage_name(stage):
    if stage == "gate0":
        return "Gate_initial"
    if stage.startswith("gate"):
        return "Gate_final"
    if stage.startswith("critic"):
        return "Critic"
    if stage.startswith("optimizer"):
        return "Optimizer"
    return {"planner": "Planner", "researcher": "Researcher", "writer": "Writer", "eval_initial": "initial_eval", "eval_final": "final_eval"}.get(stage)


def _activity(planned, rows, attempts, origins, result, cohort):
    rows_by_id = {r["task_id"]: r for r in rows}
    computed = {r["task_id"]: r for r in result["items"]}
    records = []
    for task in planned:
        task_id = task["task_id"]
        row, item = rows_by_id[task_id], computed[task_id]
        own = [a for a in attempts if a["task_id"] == task_id]
        batch_calls = [a for a in attempts if a["role"] == "memory" and a["batch_id"] == task["batch_id"]]
        out = dict(task_id=task_id, cohort=cohort, condition=task["condition"], source_task_id=task.get("source_task_id", ""),
                   batch_id=task["batch_id"], source_natural_batch=task.get("source_batch_id", task["batch_id"]),
                   record_source=origins[task_id], execution_status=item["execution_status"],
                   H1_technical_complete="O" if item["technical_complete"] else "X")
        for stage in STAGES:
            calls = [a for a in own if _stage_name(a["stage"]) == stage]
            successes = sum(a["status"] == "success" for a in calls)
            source = "new_api_success" if successes else "new_api_attempt_no_success" if calls else "not_attempted"
            if cohort == "mixed" and stage in {"Planner", "Researcher", "Writer"}:
                source = "reused_original_artifact" if own or origins[task_id] != "planned_only" else "planned_original_reuse"
                if stage == "Writer" and task["condition"] != "unchanged":
                    source = "frozen_injected_draft" if "initial" in task else "planned_injected_draft"
            if stage == "final_eval" and row.get("evaluation_reused") is True:
                if calls:
                    # A failed distinct final-eval attempt followed by valid reuse
                    # would require an explicit protocol deviation; report both.
                    source = "reused_initial_evaluation_with_separate_attempts"
                else:
                    source = "reused_initial_evaluation"
            out[stage] = "O" if calls else "X"
            out[stage + "_attempts"] = len(calls)
            out[stage + "_successes"] = successes
            out[stage + "_source"] = source
        out.update(
            LessonCurator_scope="batch_operation_not_per_task" if cohort == "natural" else "saved_per_task_lessons_no_new_curator",
            natural_batch_Curator_new_api="O" if batch_calls else "X",
            natural_batch_Curator_attempts=len(batch_calls),
            selected_lesson_count=len(row["selected_lessons"]) if isinstance(row.get("selected_lessons"), list) else "",
            initial_low=item["initial_low"], final_low=item["final_low"],
            initial_total=item["initial_total"], final_total=item["final_total"],
            initial_chars=len(row["initial"]["body"]) if isinstance(row.get("initial"), dict) and isinstance(row["initial"].get("body"), str) else "",
            final_chars=item["final_chars"], refinement_cycles=item["refinement_cycles"],
            first_critic_instructions=item["first_critic_instructions"], text_changed=item["text_changed"],
            evaluation_reused=row.get("evaluation_reused", ""),
            production_known_usage_cost_usd=item["known_usage_cost_usd"],
            production_unknown_reservation_usd=item["unknown_reservation_usd"],
        )
        records.append(out)
    return records


def build_reports(workspace, output_dir):
    """Build both planned-125 cohort reports without altering any raw record."""
    workspace = Path(workspace).resolve()
    output_dir = Path(output_dir).resolve()
    for protected in ("started", "results", "tasks", "production"):
        root = workspace / protected
        if output_dir == root or root in output_dir.parents:
            raise ValueError("Reports must not be written inside a raw-record directory")
    reads = {}
    plan = _json(workspace / "execution_plan.json", reads)
    mixed_path = workspace / "mixed_inputs.json"
    mixed = _json(mixed_path, reads) if mixed_path.exists() else None
    if mixed is not None and mixed.get("plan_sha256") != reads[str(workspace / "execution_plan.json")]:
        raise ValueError("Mixed manifest does not reference current execution plan")
    cohorts = _planned_cohorts(plan, mixed)
    expected = {t["task_id"]: dict(t, cohort=name) for name, tasks in cohorts.items() for t in tasks}
    if len(expected) != 250:
        raise ValueError("Natural and mixed task IDs overlap")
    attempts, unresolved, excluded = _attempts(workspace, expected, reads)
    analyses, activities, origins = {}, {}, {}
    role_cost_rows, batch_rows, latency_rows, text_rows = [], [], [], []
    for cohort, planned in cohorts.items():
        rows, origins[cohort] = _task_rows(workspace, planned, attempts[cohort], reads)
        result = analyze(rows, attempts[cohort], expected_task_ids=[t["task_id"] for t in planned], condition=cohort,
                         expected_batch_by_task={t["task_id"]: t["batch_id"] for t in planned})
        result["report_status"] = "not_started" if not attempts[cohort] else "completed" if result["h1"]["complete"] == 125 and result["h3"]["valid_pairs_descriptive"]["n_valid_pairs"] == 125 else "in_progress_or_incomplete"
        result["h1"]["final_verdict_available"] = result["report_status"] == "completed"
        result["report_provenance"] = dict(
            workspace=str(workspace), natural_and_mixed_share_sources=True,
            mixed_inputs_available=mixed is not None,
            task_record_sources=dict(Counter(origins[cohort].values())),
            unresolved_started_calls=[a["key"] for a in attempts[cohort] if a.get("report_synthesized")],
            note="O means a newly attempted API call in this cohort; success, reuse, quality, and task completion are distinct.",
        )
        analyses[cohort] = result
        for role, statistics in result["latency"]["by_role_attempt"].items():
            latency_rows.append(dict(cohort=cohort, scope="role_attempt", role=role, unit="ms", **statistics))
        for metric in ("task_production_call_sum", "task_production_wall_clock"):
            latency_rows.append(dict(cohort=cohort, scope=metric, role="all_direct_production", unit="ms", **result["latency"][metric]))
        for item in result["items"]:
            for stage in ("initial", "final"):
                text_rows.append(dict(cohort=cohort, task_id=item["task_id"], stage=stage,
                                      execution_status=item["execution_status"], **item[stage + "_text_metrics"]))
        activities[cohort] = _activity(planned, rows, attempts[cohort], origins[cohort], result, cohort)
        for role in ROLES:
            ledger = result["role_cost_ledger"].get(role, {})
            own = [a for a in attempts[cohort] if a["role"] == role]
            known = ledger.get("known_usage_cost_usd", 0.)
            reserved = ledger.get("unknown_reservation_usd", 0.)
            role_cost_rows.append(dict(
                cohort=cohort, role=role, attempts=len(own), successful_attempts=sum(a["status"] == "success" for a in own),
                failed_or_pending_attempts=sum(a["status"] != "success" for a in own),
                known_usage_cost_usd=known, unknown_reservation_usd=reserved,
                unknown_usage_attempts=ledger.get("unknown_usage_attempts", 0),
                budget_ledger_usd=known + reserved, included_in_H2=role != "evaluator" and (cohort == "natural" or role in {"gate", "critic", "optimizer"}),
                scope="batch operation, not per-task invocation" if role == "memory" else "measurement" if role == "evaluator" else "production",
            ))
        for batch_id in (1, 2, 3, 4):
            own = [a for a in attempts[cohort] if a["role"] == "memory" and a["batch_id"] == batch_id]
            batch_rows.append(dict(
                cohort=cohort, batch_id=batch_id, planned_tasks=sum(t["batch_id"] == batch_id for t in planned),
                Curator_new_api="O" if own else "X", attempts=len(own), successful_attempts=sum(a["status"] == "success" for a in own),
                known_usage_cost_usd=sum(a["cost_usd"] or 0. for a in own),
                unknown_reservation_usd=sum(a.get("unknown_cost_reservation_usd", a.get("budget_charge_usd", 0.)) for a in own if a.get("cost_usd") is None),
                interpretation="After-batch Curator operation; never multiply by task count" if cohort == "natural" else "No new Curator; original per-task selected lessons reused",
            ))
    for path, digest in reads.items():
        if _sha(Path(path).read_bytes()) != digest:
            raise RuntimeError("Input changed while reporting; rerun for a consistent snapshot: " + path)
    output_dir.mkdir(parents=True, exist_ok=True)
    for cohort, result in analyses.items():
        _write_json(output_dir / f"{cohort}_analysis.json", result)
        _write_csv(output_dir / f"{cohort}_activity_125.csv", activities[cohort])
    _write_csv(output_dir / "latency_descriptive.csv", latency_rows)
    _write_csv(output_dir / "text_metrics_500.csv", text_rows)
    _write_csv(output_dir / "role_costs.csv", role_cost_rows)
    _write_csv(output_dir / "batch_curator_activity.csv", batch_rows)
    readme = """# Study E final reports

These files are derived from immutable local records; this program makes no API calls.
Each cohort retains its 125 planned tasks, including missing or unfinished records.
report_status=not_started or in_progress_or_incomplete is a progress snapshot,
not a final experimental result. Planned-only 0/125 is not an observed final failure.
The two cohorts share 125 source tasks and are not 250 independent observations.

O = at least one NEW API attempt for that stage in this cohort; X = no new attempt.
O does not mean success, correctness, text change, or quality improvement.
The adjacent attempt/success/source columns distinguish these cases. A resumed call
served from a previously successful result is still one original call, not another API attempt.
Mixed Planner/Researcher/Writer are X with artifact reuse; final evaluation is X when
the recorded exact-text reuse rule supplies the initial evaluation.

Lesson Curator operates after a natural batch, not once per task. Repeated batch
columns in task CSVs are context only: count calls from batch_curator_activity.csv.
The mixed cohort makes no new Curator calls and reuses saved per-task lessons.

tasks/{id}.json takes precedence over production/{id}.json. A production checkpoint
can establish technical completion while evaluation is missing; it does not invent
an outcome. Successful evaluation attempts may fill checkpoint measurement fields.
Unresolved started calls are charged their unknown reservation in memory only; no
raw result is written or overwritten. Unknown production usage makes primary H2
undetermined. Reservations remain separate budget records, not observed usage cost.

H3 missing pairs prevent a full-cohort primary point verdict. Valid-pair descriptive
counts and missing counts remain visible. Few initial events are reported without
an invented scientific minimum of ten. H1/H2/H3 are Proposal point criteria.

Numerical analyses follow Proposal.pdf pp.5-6: completion, production cost CV,
low-quality relative reduction, descriptive cost/latency/four quality dimensions,
body-only English Flesch ease/grade, word count and unique-token/word-count lexical
diversity, and the paired four-score-total Wilcoxon test (two-sided alpha=.05,
Pratt zero handling, asymptotic method without continuity correction). Missing
pairs prevent the full-cohort test; unchanged pairs are retained. The Wilcoxon
null is not the H3 30% boundary. Shared evolving memory limits reference inference.
No additional inferential procedures or numeric Gate subset/crosstab are generated.
Raw Gate and O/X audit fields remain available without adding statistical tests.

Text metrics describe English surface form, not factual correctness. See JSON
analysis_settings for frozen formulas and token/syllable rules. CSV contains 500
planned text rows; absent body values remain missing, not deleted. Latency role
rows count all attempted calls, including failed or pending calls. Task call-sum
excludes evaluation and batch Curator and is not wall-clock. Wall-clock uses the
first direct production attempt to production completion, with waits and resumes.
Missing timestamps/latencies are not zero; known partial sums are audit fields.

No report is a substitute for preregistration, source/trace verification, or invoice reconciliation.
"""
    (output_dir / "README.md").write_text(readme, encoding="utf-8")
    receipt = dict(
        created_at=datetime.now(timezone.utc).isoformat(), workspace=str(workspace), output_dir=str(output_dir),
        planned_n={k: len(v) for k, v in cohorts.items()}, mixed_input_manifest_available=mixed is not None,
        rows_written={k: len(v) for k, v in activities.items()},
        attempt_counts={k: len(v) for k, v in attempts.items()}, unresolved_started_calls=unresolved,
        excluded_outside_planned_cohorts=excluded, source_sha256=reads, source_snapshot_unchanged=True,
        implementation_sha256={str(p): _sha(p.read_bytes()) for p in (HERE / "analysis.py", Path(__file__).resolve())},
        no_api_calls=True,
    )
    receipt["output_sha256"] = {p.name: _sha(p.read_bytes()) for p in sorted(output_dir.iterdir()) if p.is_file() and p.name in {
        "natural_analysis.json", "mixed_analysis.json", "natural_activity_125.csv", "mixed_activity_125.csv", "role_costs.csv", "batch_curator_activity.csv", "latency_descriptive.csv", "text_metrics_500.csv", "README.md"}}
    _write_json(output_dir / "report_manifest.json", receipt)
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=DEFAULT_WORKSPACE)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    receipt = build_reports(args.workspace, args.output or args.workspace / "reports")
    print(json.dumps({k: receipt[k] for k in ("output_dir", "rows_written", "attempt_counts", "no_api_calls")}, ensure_ascii=False))
