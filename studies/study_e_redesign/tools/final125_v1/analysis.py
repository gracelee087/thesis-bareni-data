"""Offline Study E analyses restricted to Proposal.pdf (pp. 5-6).

analyze(rows, attempts, expected_task_ids=..., condition="natural"|"mixed")
retains every planned task. Missing values are never passes or zero-cost calls.
No provider calls; usage-priced costs are not reconciled provider invoices.
"""
from __future__ import annotations
import argparse
import json
import math
import re
import statistics
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

DIMENSIONS = ("persona_fit", "clarity", "actionability", "factual_grounding")
LENGTH_LIMITS = (150, 2000)
PRODUCTION_ROLES = {"planner", "researcher", "writer", "gate", "critic", "optimizer", "memory"}
WORDS = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)?")
TEXT_METRICS = ("flesch_reading_ease", "flesch_kincaid_grade", "word_count", "lexical_diversity_ttr")


def _number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _scores(value):
    if not isinstance(value, dict):
        return None
    scores = value.get("scores", value)
    if not isinstance(scores, dict) or any(k not in scores for k in DIMENSIONS):
        return None
    result = [scores[k] for k in DIMENSIONS]
    if not all(_number(x) and int(x) == x and 1 <= x <= 5 for x in result):
        return None
    if value.get("critical_violation") is True and 1 not in result:
        return None
    if "critical_violation" in value and not isinstance(value["critical_violation"], bool):
        return None
    if "total_score" in value and value["total_score"] != sum(result):
        return None
    if "pass" in value and (not isinstance(value["pass"], bool) or value["pass"] != (min(result) >= 3)):
        return None
    return result


def _body(row, stage):
    value = row.get(stage + "_body")
    if value is None and isinstance(row.get(stage), dict):
        value = row[stage].get("body")
    return value if isinstance(value, str) else None


def _cv(values):
    return statistics.stdev(values) / statistics.mean(values) if len(values) >= 2 and statistics.mean(values) > 0 else None


def _quantile(values, p):
    if not values:
        return None
    values = sorted(values)
    x = (len(values) - 1) * p
    lo, hi = math.floor(x), math.ceil(x)
    return values[lo] + (values[hi] - values[lo]) * (x - lo)


def describe(values, expected_n=None):
    valid = [x for x in values if _number(x)]
    expected_n = len(values) if expected_n is None else expected_n
    return dict(n_observed=len(valid), n_missing=expected_n - len(valid),
                mean=statistics.mean(valid) if valid else None,
                sample_sd=statistics.stdev(valid) if len(valid) >= 2 else None,
                median=_quantile(valid, .5), p95=_quantile(valid, .95),
                minimum=min(valid) if valid else None, maximum=max(valid) if valid else None)


def _syllables(word):
    value = re.sub(r"[^a-z]", "", word.casefold())
    count = len(re.findall(r"[aeiouy]+", value))
    if value.endswith("e") and count > 1 and not value.endswith(("le", "ye")):
        count -= 1
    return max(1, count) if value else 0


def text_metrics(text):
    """English body-only heuristics; missing/wordless readability is undefined."""
    if not isinstance(text, str):
        return {k: None for k in TEXT_METRICS}
    words = WORDS.findall(text)
    count = len(words)
    sentences = max(1, len(re.findall(r"[.!?]+(?:\s|$)", text))) if text.strip() else 0
    syllables = sum(_syllables(word) for word in words)
    return dict(word_count=count,
                lexical_diversity_ttr=len({w.casefold() for w in words}) / count if count else None,
                flesch_reading_ease=206.835 - 1.015 * count / sentences - 84.6 * syllables / count if count and sentences else None,
                flesch_kincaid_grade=.39 * count / sentences + 11.8 * syllables / count - 15.59 if count and sentences else None)


def paired_wilcoxon(items):
    pairs = [x for x in items if x["initial_total"] is not None and x["final_total"] is not None]
    result = dict(n_planned=len(items), n_valid_pairs=len(pairs), alpha=.05, alternative="two-sided",
                  zero_method="pratt", method="asymptotic", correction=False,
                  statistic=None, p_value=None, rejects_zero_change_at_005=None,
                  note="Paired sum of four 1-5 scores, final minus initial. This tests a signed-rank location null, not H3's 30% boundary. Shared evolving memory and non-independent tasks limit reference inference; no causal interpretation.")
    if len(pairs) != len(items):
        result["status"] = "undetermined_missing_pairs"
        return result
    differences = [x["final_total"] - x["initial_total"] for x in pairs]
    if not any(differences):
        result.update(status="all_differences_zero", statistic=0., p_value=1., rejects_zero_change_at_005=False)
        return result
    import scipy
    from scipy.stats import wilcoxon
    test = wilcoxon(differences, zero_method="pratt", alternative="two-sided", correction=False, method="asymptotic")
    result.update(status="computed_reference", scipy_version=scipy.__version__, statistic=float(test.statistic),
                  p_value=float(test.pvalue), rejects_zero_change_at_005=bool(test.pvalue < .05))
    return result


def _pair_summary(items):
    paired = [x for x in items if x["initial_low"] is not None and x["final_low"] is not None]
    trans = Counter((x["initial_low"], x["final_low"]) for x in paired)
    b, f = sum(x["initial_low"] for x in paired), sum(x["final_low"] for x in paired)
    return dict(n_planned_in_group=len(items), n_valid_pairs=len(paired), n_missing_pairs=len(items) - len(paired),
                initial_low=b, final_low=f, relative_reduction=(b-f)/b if b else None,
                repaired=trans[True, False], harmed=trans[False, True], stayed_low=trans[True, True], stayed_pass=trans[False, False])


def _attempt_accounting(attempts, expected_ids, rows_by_id, condition, expected_batch_by_task):
    ids, batches = set(expected_ids), defaultdict(list)
    if expected_batch_by_task is None:
        expected_batch_by_task = {t: 1 + (i >= 31) + (i >= 62) + (i >= 93) if len(expected_ids) == 125 else rows_by_id.get(t, {}).get("batch_id", 1) for i, t in enumerate(expected_ids)}
    for task_id in expected_ids:
        if task_id not in expected_batch_by_task:
            raise ValueError("Missing expected batch assignment: " + task_id)
        batches[str(expected_batch_by_task[task_id])].append(task_id)
    by_task = {t: dict(known_usage_cost_usd=0., unknown_reservation_usd=0., unknown_usage_attempts=0) for t in expected_ids}
    by_role = defaultdict(lambda: dict(attempts=0, known_usage_cost_usd=0., unknown_reservation_usd=0., unknown_usage_attempts=0))
    normalized, seen = [], set()
    for original in attempts:
        attempt = dict(original)
        key = attempt.get("key", "")
        if key and key in seen:
            raise ValueError("Duplicate attempt key: " + key)
        if key:
            seen.add(key)
        role, task_id = str(attempt.get("role", "")).lower(), attempt.get("task_id")
        if task_id is None:
            matches = [t for t in expected_ids if key.startswith(t + "_")]
            if len(matches) == 1:
                task_id = matches[0]
        if not role and task_id is not None:
            role = re.sub(r"[012]$", "", key[len(task_id) + 1:].split("__")[0])
        role = {"curator": "memory", "lesson_curator": "memory", "eval_initial": "evaluator", "eval_final": "evaluator", "judge_eval_initial": "evaluator", "judge_eval_final": "evaluator"}.get(role, role)
        if role not in PRODUCTION_ROLES | {"evaluator"}:
            raise ValueError("Unknown attempt role; explicit normalization required: " + role)
        if task_id is not None and task_id not in ids:
            raise ValueError("Attempt outside planned cohort: " + str(task_id))
        if role != "memory" and task_id is None:
            raise ValueError("Task attempt needs a planned task_id")
        if condition == "mixed" and role not in {"gate", "critic", "optimizer", "evaluator"}:
            raise ValueError("Mixed cost ledger contains new upstream/curator calls")
        cost = attempt.get("cost_usd")
        if cost is not None and (not _number(cost) or cost < 0):
            raise ValueError("Invalid known usage cost")
        unknown = cost is None
        reserve = attempt.get("unknown_cost_reservation_usd", attempt.get("unknown_reservation_usd"))
        if reserve is None:
            reserve = attempt.get("budget_charge_usd", 0.) if unknown else 0.
        if not _number(reserve) or reserve < 0 or (not unknown and reserve):
            raise ValueError("Reservation must be nonnegative and restricted to unknown usage")
        latency = attempt.get("latency_ms")
        if latency is not None and (not _number(latency) or latency < 0):
            raise ValueError("Invalid latency_ms")
        attempt.update(role=role, task_id=task_id)
        normalized.append(attempt)
        ledger = by_role[role]
        ledger["attempts"] += 1
        ledger["known_usage_cost_usd"] += cost or 0.
        ledger["unknown_reservation_usd"] += reserve
        ledger["unknown_usage_attempts"] += int(unknown)
        if role == "evaluator":
            continue
        if role == "memory":
            batch_id = attempt.get("batch_id")
            if batch_id is None:
                match = re.search(r"(?:batch_|batch)(\d+)", key)
                batch_id = match.group(1) if match else None
            targets = batches.get(str(batch_id), [])
            if not targets:
                raise ValueError("Curator attempt needs a valid batch_id")
        else:
            targets = [task_id]
        for target in targets:
            by_task[target]["known_usage_cost_usd"] += (cost or 0.) / len(targets)
            by_task[target]["unknown_reservation_usd"] += reserve / len(targets)
            by_task[target]["unknown_usage_attempts"] += int(unknown)
    for role, ledger in by_role.items():
        own = [a for a in normalized if a["role"] == role]
        ledger["per_attempt_known_cost_descriptive_usd"] = describe([a.get("cost_usd") for a in own])
    return by_task, dict(by_role), normalized


def _timestamp(value):
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo is not None else None
    except ValueError:
        return None


def _task_latency(task_id, row, attempts):
    own = [a for a in attempts if a["task_id"] == task_id and a["role"] in PRODUCTION_ROLES - {"memory"}]
    measured = [a["latency_ms"] for a in own if a.get("latency_ms") is not None]
    complete = row.get("execution_status", row.get("status")) == "complete"
    starts = [_timestamp(a.get("created_at")) for a in own]
    end = _timestamp(row.get("production_completed_at"))
    wall = (end - min(starts)).total_seconds() * 1000 if complete and starts and all(s is not None for s in starts) and end is not None else None
    if wall is not None and wall < 0:
        raise ValueError("Production completion predates first attempt: " + task_id)
    return dict(production_attempts=len(own), measured_attempts=len(measured), missing_attempt_latency=len(own)-len(measured),
                known_attempt_latency_sum_ms=sum(measured) if own else None,
                production_call_sum_ms=sum(measured) if complete and own and len(measured) == len(own) else None,
                production_wall_clock_ms=wall)


def analyze(rows, attempts, *, expected_task_ids, condition, expected_batch_by_task=None):
    """All planned tasks remain; only Proposal-defined metrics and operational audit."""
    if condition not in {"natural", "mixed"}:
        raise ValueError("condition must be natural or mixed")
    expected_ids = list(expected_task_ids)
    if not expected_ids or len(set(expected_ids)) != len(expected_ids):
        raise ValueError("Planned task IDs must be unique and nonempty")
    by_id = {}
    for row in rows:
        task_id = row["task_id"]
        if task_id in by_id or task_id not in expected_ids:
            raise ValueError("Duplicate or unplanned task: " + task_id)
        by_id[task_id] = row
    costs, roles, calls = _attempt_accounting(attempts, expected_ids, by_id, condition, expected_batch_by_task)
    items = []
    for task_id in expected_ids:
        row = by_id.get(task_id, {})
        initial, final = _scores(row.get("initial_eval")), _scores(row.get("final_eval"))
        status = row.get("execution_status", row.get("status", "missing"))
        initial_body, body = _body(row, "initial"), _body(row, "final")
        cycles = row.get("cycles", [])
        repairs = cycles[0].get("critique", {}).get("repairs") if cycles else None
        completed = status == "complete" and body is not None and LENGTH_LIMITS[0] <= len(body) <= LENGTH_LIMITS[1]
        items.append(dict(task_id=task_id, stratum=row.get("condition", row.get("defect_type", condition)),
                          execution_status=status, technical_complete=completed,
                          initial_low=min(initial) < 3 if initial else None, final_low=min(final) < 3 if final else None,
                          initial_total=sum(initial) if initial else None, final_total=sum(final) if final else None,
                          initial_scores=dict(zip(DIMENSIONS, initial)) if initial else None,
                          final_scores=dict(zip(DIMENSIONS, final)) if final else None,
                          initial_text_metrics=text_metrics(initial_body), final_text_metrics=text_metrics(body),
                          initial_chars=len(initial_body) if initial_body is not None else None,
                          final_chars=len(body) if body is not None else None,
                          first_critic_instructions=bool(repairs) if isinstance(repairs, list) else None,
                          text_changed=(initial_body != body or row.get("initial", {}).get("title", row.get("initial_title")) != row.get("final", {}).get("title", row.get("final_title"))) if initial_body is not None and body is not None else None,
                          evaluation_reused=row.get("evaluation_reused"), refinement_cycles=row.get("refinement_cycles", len(cycles)),
                          latency=_task_latency(task_id, row, calls), **costs[task_id]))
    n, complete = len(items), sum(x["technical_complete"] for x in items)
    summary = _pair_summary(items)
    full_pairs = summary["n_valid_pairs"] == n
    known = [x["known_usage_cost_usd"] for x in items]
    unknown = sum(v["unknown_usage_attempts"] for k, v in roles.items() if k in PRODUCTION_ROLES)
    cost_determined = complete == n and any(a["role"] in PRODUCTION_ROLES for a in calls) and unknown == 0
    cv = _cv(known) if cost_determined else None
    relative = summary["relative_reduction"] if full_pairs else None
    score_descriptions = {}
    text_descriptions = {}
    for metric in (*DIMENSIONS, "total_score"):
        def score(item, stage):
            return item[stage + "_total"] if metric == "total_score" else (item[stage + "_scores"] or {}).get(metric)
        before, after = [score(x, "initial") for x in items], [score(x, "final") for x in items]
        score_descriptions[metric] = dict(initial=describe(before), final=describe(after), paired_change=describe([f-b if b is not None and f is not None else None for b, f in zip(before, after)]))
    for metric in TEXT_METRICS:
        before = [x["initial_text_metrics"][metric] for x in items]
        after = [x["final_text_metrics"][metric] for x in items]
        text_descriptions[metric] = dict(initial=describe(before), final=describe(after), paired_change=describe([f-b if b is not None and f is not None else None for b, f in zip(before, after)]))
    return dict(
        schema_version=2, numerical_policy="Proposal.pdf pp.5-6 only", run_condition=condition, planned_n=n,
        h1=dict(complete=complete, denominator=n, rate=complete/n, point_criterion_90pct_met=complete/n >= .90,
                noncomplete_task_ids=[x["task_id"] for x in items if not x["technical_complete"]],
                note="Technical completion under frozen recovery/budget policy, not quality. Pending records are not final failures."),
        h2=dict(status="measured_usage_priced" if cost_determined else "undetermined_incomplete_or_unknown_usage",
                production_scope="all production plus within-batch equally allocated Curator; excludes evaluator" if condition == "natural" else "new Gate/Critic/Optimizer retries only; excludes reused upstream and evaluator",
                cv=cv, point_criterion_cv_below_025_met=cv < .25 if cv is not None else None,
                per_task_production_cost_descriptive_usd=describe(known if cost_determined else [None]*n),
                known_usage_cost_usd=sum(known), unknown_reservation_usd=sum(x["unknown_reservation_usd"] for x in items), unknown_usage_attempts=unknown,
                note="Known usage priced at frozen rates, not invoices. Reservations are separate budget records, never observed cost, imputed zero, or a CV bound."),
        h3=dict(status="missing_measurements" if not full_pairs else "undefined_zero_initial_low" if relative is None else "measured",
                relative_reduction=relative, point_criterion_30pct_met=relative >= .30 if relative is not None else None,
                initial_event_count=summary["initial_low"] if full_pairs else None, ten_event_cutoff_used=False,
                valid_pairs_descriptive=summary,
                note="Few events remain reportable; no minimum of ten or power guarantee. Missing pairs prevent the full-cohort primary verdict. Transition counts only explain B-F; no additional hypothesis tests.",
                scope="Fixed-AI natural pre/post quality" if condition == "natural" else "Fixed-AI controlled-mixture repair, not natural failure prevalence"),
        quality_scores=score_descriptions, text_metrics=text_descriptions,
        paired_total_wilcoxon=paired_wilcoxon(items),
        latency=dict(unit="milliseconds", by_role_attempt={role: describe([a.get("latency_ms") for a in calls if a["role"] == role]) for role in sorted(roles)},
                     task_production_call_sum=describe([x["latency"]["production_call_sum_ms"] for x in items]),
                     task_production_wall_clock=describe([x["latency"]["production_wall_clock_ms"] for x in items]),
                     definition="Role distributions include successful, failed, and unresolved attempts; missing timings stay missing. Task call-sum adds direct production attempts including retries, excluding evaluator and batch Curator; it is not elapsed wall time. Wall-clock is first direct production attempt created_at to production_completed_at, including in-task waits and resumes; missing endpoints are undefined. Batch Curator is separately reported by role, never duplicated as task latency."),
        role_cost_ledger=roles, items=items,
        analysis_settings=dict(hard_body_chars=list(LENGTH_LIMITS), body_only_text_statistics=True,
             english_tokenization="[A-Za-z]+(?:'[A-Za-z]+)?", sentence_rule="[.!?]+ followed by whitespace or end; minimum one for nonempty text",
             syllable_rule="English vowel groups; subtract terminal e except le/ye when count>1; minimum one per word",
             text_metric_note="Flesch ease=206.835-1.015(W/S)-84.6(Y/W); grade=.39(W/S)+11.8(Y/W)-15.59; lexical diversity=casefolded unique tokens/W. English heuristic, length-dependent; not evidence of factual truth or rubric validity.",
             expected_order_used_for_batch_allocation=expected_batch_by_task is None))


def _self_test():
    def ev(low=False):
        return {"scores": dict(zip(DIMENSIONS, [2 if low else 4, 4, 4, 4]))}
    ids = ["T1", "T2", "T3", "T4"]
    rows = [dict(task_id=t, status="complete", batch_id=1, condition="unchanged", initial={"body": "A clear task. " * 20}, final={"body": "A clear task. " * 20}, initial_eval=ev(i == 0), final_eval=ev(i == 1), cycles=[{}]) for i, t in enumerate(ids)]
    attempts = [dict(task_id=t, role="optimizer", cost_usd=.02, latency_ms=100) for t in ids]
    result = analyze(rows, attempts, expected_task_ids=ids, condition="mixed")
    assert result["h1"]["complete"] == 4 and result["h2"]["cv"] == 0
    assert result["h3"]["relative_reduction"] == 0 and result["h3"]["valid_pairs_descriptive"]["repaired"] == 1
    assert result["h3"]["valid_pairs_descriptive"]["harmed"] == 1
    unknown = analyze(rows, attempts + [dict(task_id="T1", role="gate", cost_usd=None, budget_charge_usd=.5)], expected_task_ids=ids, condition="mixed")
    assert unknown["h2"]["cv"] is None and unknown["latency"]["task_production_call_sum"]["n_missing"] == 1
    missing = analyze(rows[:3], attempts, expected_task_ids=ids, condition="mixed")
    assert missing["h1"]["denominator"] == 4 and missing["h1"]["complete"] == 3
    assert missing["h3"]["relative_reduction"] is None and missing["paired_total_wilcoxon"]["p_value"] is None
    natural = analyze(rows, attempts + [dict(role="memory", batch_id=1, cost_usd=.04)], expected_task_ids=ids, condition="natural")
    assert all(abs(x["known_usage_cost_usd"] - .03) < 1e-12 for x in natural["items"])
    assert _scores(dict(ev(), critical_violation=True)) is None
    assert _scores(dict(ev(), **{"pass": False})) is None
    assert _scores(dict(ev(), total_score=4)) is None
    print("offline Proposal-only analysis checks passed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.self_test:
        _self_test()
    elif args.input:
        result = analyze(**json.loads(args.input.read_text(encoding="utf-8-sig")))
        rendered = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)
        if args.output:
            args.output.write_text(rendered + "\n", encoding="utf-8")
        else:
            print(rendered)
    else:
        parser.error("use --self-test or --input")
