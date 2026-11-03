from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import random
import re
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from evaluator_selection_schema import EvaluatorRating, Usage, google_json_schema


STUDY = Path(__file__).resolve().parents[2]
REPOSITORY = STUDY.parents[1]
PRIVATE = STUDY / "private"
CONFIG_PATH = STUDY / "19_EVALUATOR_PRICE_MATCHED_CONFIG.json"
PROMPT_PATH = STUDY / "13_EVALUATOR_PROMPT.md"
PROTOCOL_PATH = STUDY / "19_EVALUATOR_PRICE_MATCHED_PROTOCOL.md"
SELECTION_PROTOCOL_PATH = STUDY / "04_EVALUATOR_SELECTION_PROTOCOL.md"
BLIND_PATH = STUDY / "08_BLIND_RATING_PACKET.md"
CONSTRUCTION_MANIFEST_PATH = PRIVATE / "08_BLIND_MANIFEST_PRIVATE.json"
RUBRIC_PATH = STUDY.parents[0] / "study_d" / "config" / "rubric.md"
ROUND1_PATH = STUDY / "10_AUTHOR_RATING_ROUND1_RAW.md"
RERATE_PATH = STUDY / "11_AUTHOR_RATING_RERATE_RAW.md"
REFERENCE_REPORT_PATH = STUDY / "12_AUTHOR_REFERENCE_VALIDATION_RESULTS.md"
INPUT_PATH = PRIVATE / "v3" / "13_EVALUATOR_INPUTS.json"
SCHEDULE_PATH = PRIVATE / "v3" / "13_EVALUATOR_SCHEDULE.json"
FREEZE_PATH = PRIVATE / "v3" / "13_EVALUATOR_RUN_FREEZE.json"
ACCESS_RECEIPT_PATH = PRIVATE / "v3" / "13_EVALUATOR_ACCOUNT_ACCESS.json"
RESULTS_DIR = PRIVATE / "v3" / "evaluator_results"
SUMMARY_PATH = PRIVATE / "v3" / "evaluator_results_summary.json"


class FreezeError(RuntimeError):
    pass


class CostCapError(RuntimeError):
    pass


@dataclass
class ProviderEnvelope:
    raw_text: str
    provider_response: Any
    usage: Usage
    stop_reason: str | None
    response_id: str | None


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def write_new_or_identical(path: Path, value: Any) -> None:
    payload = canonical_bytes(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != payload:
            raise FreezeError(f"refusing to overwrite changed file: {path}")
        return
    with path.open("xb") as handle:
        handle.write(payload)


def write_terminal(path: Path, value: Any) -> None:
    payload = canonical_bytes(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(payload)


def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def load_environment() -> None:
    from dotenv import load_dotenv

    load_dotenv(REPOSITORY / ".env", override=False)


def markdown_field(block: str, label: str) -> str:
    match = re.search(rf"(?m)^- {re.escape(label)}: `(.+)`\s*$", block)
    if not match:
        raise FreezeError(f"missing {label!r} in blind item")
    return match.group(1)


def parse_blind_packet() -> dict:
    text = BLIND_PATH.read_text(encoding="utf-8")
    common_marker = "## Common Bareni evidence for every item"
    if common_marker not in text:
        raise FreezeError("common evidence section is missing")
    common = text.split(common_marker, 1)[1].split("\n---", 1)[0].strip()
    parts = re.split(r"(?m)^## (EVAL-BLIND-\d{3})\s*$", text)
    items = []
    for index in range(1, len(parts), 2):
        item_id = parts[index]
        block = parts[index + 1]
        body_match = re.search(
            r"(?ms)^- Body \((\d+) characters\):\s*\r?\n\r?\n> (.*?)\r?\n\r?\n### Author rating",
            block,
        )
        if not body_match:
            raise FreezeError(f"body missing for {item_id}")
        body = body_match.group(2).replace("\n> ", "\n").strip()
        declared = int(body_match.group(1))
        if len(body) != declared:
            raise FreezeError(f"character count mismatch for {item_id}")
        items.append(
            {
                "item_id": item_id,
                "topic": markdown_field(block, "Topic"),
                "task_brief": markdown_field(block, "Task brief"),
                "task_evidence": markdown_field(block, "Task-specific evidence"),
                "title": markdown_field(block, "Title"),
                "body": body,
                "character_count": len(body),
            }
        )
    expected = [f"EVAL-BLIND-{number:03d}" for number in range(1, 31)]
    observed = [item["item_id"] for item in items]
    if observed != expected:
        raise FreezeError(f"expected ordered IDs 001..030, got {observed}")
    return {
        "schema_version": "study-e-evaluator-inputs-v1",
        "blind_packet_sha256": sha256_file(BLIND_PATH),
        "common_evidence": common,
        "items": items,
    }


def parse_prompt() -> tuple[str, str]:
    text = PROMPT_PATH.read_text(encoding="utf-8")
    try:
        system = text.split("## System prompt", 1)[1].split("## User prompt template", 1)[0].strip()
        template = text.split("## User prompt template", 1)[1].strip()
    except IndexError as exc:
        raise FreezeError("prompt file sections are malformed") from exc
    required = {"{item_id}", "{common_evidence}", "{task_brief}", "{task_evidence}", "{title}", "{body}"}
    if not all(token in template for token in required):
        raise FreezeError("user prompt template is missing a required placeholder")
    return system, template


def build_user_prompt(template: str, common: str, item: dict) -> str:
    return template.format(common_evidence=common, **item)


def build_schedule(config: dict, inputs: dict) -> dict:
    rows = []
    for candidate in config["candidates"]:
        for item in inputs["items"]:
            rows.append(
                {
                    "candidate_id": candidate["candidate_id"],
                    "provider": candidate["provider"],
                    "model": candidate["model"],
                    "item_id": item["item_id"],
                }
            )
    random.Random(config["execution"]["schedule_seed"]).shuffle(rows)
    for index, row in enumerate(rows, 1):
        row["schedule_index"] = index
    expected = int(config["execution"]["planned_assessments"])
    if len(rows) != expected or len({(row["candidate_id"], row["item_id"]) for row in rows}) != expected:
        raise FreezeError("schedule is incomplete or contains duplicates")
    return {
        "schema_version": "study-e-evaluator-schedule-v1",
        "schedule_seed": config["execution"]["schedule_seed"],
        "rows": rows,
    }


def frozen_files() -> dict[str, Path]:
    return {
        "selection_protocol": SELECTION_PROTOCOL_PATH,
        "config": CONFIG_PATH,
        "prompt": PROMPT_PATH,
        "run_protocol": PROTOCOL_PATH,
        "blind_packet": BLIND_PATH,
        "construction_manifest": CONSTRUCTION_MANIFEST_PATH,
        "rubric": RUBRIC_PATH,
        "author_round1": ROUND1_PATH,
        "author_rerate": RERATE_PATH,
        "author_reference_report": REFERENCE_REPORT_PATH,
        "runner": Path(__file__).resolve(),
        "schema": Path(__file__).with_name("evaluator_selection_schema.py"),
        "analyzer": Path(__file__).with_name("analyze_evaluator_selection.py"),
        "tests": Path(__file__).with_name("test_evaluator_selection.py"),
        "smoke": Path(__file__).with_name("smoke.py"),
        "smoke_receipt": PRIVATE / "v3" / "smoke.json",
        "inputs": INPUT_PATH,
        "schedule": SCHEDULE_PATH,
        "account_access_receipt": ACCESS_RECEIPT_PATH,
    }


def freeze() -> dict:
    if RESULTS_DIR.exists() and any(RESULTS_DIR.glob("*.json")):
        raise FreezeError("candidate result files already exist; refusing to refreeze")
    config = load_config()
    smoke = json.loads((PRIVATE / "v3" / "smoke.json").read_text(encoding="utf-8"))
    if not smoke["all_valid"] or smoke["runner_sha256"] != sha256_file(Path(__file__).resolve()) or smoke["schema_sha256"] != sha256_file(Path(__file__).with_name("evaluator_selection_schema.py")):
        raise FreezeError("smoke receipt is invalid or refers to different code")
    inputs = parse_blind_packet()
    system, template = parse_prompt()
    for item in inputs["items"]:
        prompt = build_user_prompt(template, inputs["common_evidence"], item)
        if item["item_id"] not in prompt or item["body"] not in prompt:
            raise FreezeError(f"prompt assembly failed for {item['item_id']}")
    schedule = build_schedule(config, inputs)
    write_new_or_identical(INPUT_PATH, inputs)
    write_new_or_identical(SCHEDULE_PATH, schedule)
    if not ACCESS_RECEIPT_PATH.exists():
        raise FreezeError("account access receipt is missing; run access-check first")
    access = json.loads(ACCESS_RECEIPT_PATH.read_text(encoding="utf-8"))
    if not access.get("all_accessible"):
        raise FreezeError("one or more candidate model IDs were not visible to the account")
    files = frozen_files()
    missing = [str(path) for path in files.values() if not path.exists()]
    if missing:
        raise FreezeError(f"cannot freeze; missing files: {missing}")
    manifest = {
        "schema_version": "study-e-evaluator-run-freeze-v1",
        "created_on": "2026-09-05",
        "planned_assessments": config["execution"]["planned_assessments"],
        "candidate_ids": [candidate["candidate_id"] for candidate in config["candidates"]],
        "file_sha256": {name: sha256_file(path) for name, path in files.items()},
        "system_prompt_sha256": sha256_bytes(system.encode("utf-8")),
        "user_prompt_template_sha256": sha256_bytes(template.encode("utf-8")),
        "rating_json_schema_sha256": sha256_bytes(canonical_bytes(EvaluatorRating.model_json_schema(by_alias=True))),
    }
    write_new_or_identical(FREEZE_PATH, manifest)
    return manifest


def verify_freeze() -> dict:
    if not FREEZE_PATH.exists():
        raise FreezeError("freeze manifest is missing; run freeze first")
    manifest = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    for name, expected in manifest["file_sha256"].items():
        path = frozen_files()[name]
        observed = sha256_file(path)
        if observed != expected:
            raise FreezeError(f"frozen hash mismatch for {name}: {observed} != {expected}")
    system, template = parse_prompt()
    if sha256_bytes(system.encode("utf-8")) != manifest["system_prompt_sha256"]:
        raise FreezeError("system prompt hash mismatch")
    if sha256_bytes(template.encode("utf-8")) != manifest["user_prompt_template_sha256"]:
        raise FreezeError("user prompt template hash mismatch")
    schema_hash = sha256_bytes(canonical_bytes(EvaluatorRating.model_json_schema(by_alias=True)))
    if schema_hash != manifest["rating_json_schema_sha256"]:
        raise FreezeError("rating schema hash mismatch")
    return manifest


def jsonable_response(response: Any) -> Any:
    if response is None:
        return None
    if hasattr(response, "model_dump"):
        return response.model_dump(mode="json")
    if hasattr(response, "to_json_dict"):
        return response.to_json_dict()
    if hasattr(response, "to_dict"):
        return response.to_dict()
    return {"repr": repr(response)}


def anthropic_usage(response: Any) -> Usage:
    raw = getattr(response, "usage", None)
    direct = int(getattr(raw, "input_tokens", 0) or 0)
    cached = int(getattr(raw, "cache_read_input_tokens", 0) or 0)
    write = int(getattr(raw, "cache_creation_input_tokens", 0) or 0)
    return Usage(
        input_tokens=direct + cached + write,
        cached_input_tokens=cached,
        cache_write_input_tokens=write,
        output_tokens=int(getattr(raw, "output_tokens", 0) or 0),
    )


def openai_usage(response: Any) -> Usage:
    raw = getattr(response, "usage", None)
    inp = getattr(raw, "input_tokens_details", None)
    out = getattr(raw, "output_tokens_details", None)
    return Usage(
        input_tokens=int(getattr(raw, "input_tokens", 0) or 0),
        cached_input_tokens=int(getattr(inp, "cached_tokens", 0) or 0),
        cache_write_input_tokens=int(getattr(inp, "cache_write_tokens", 0) or 0),
        output_tokens=int(getattr(raw, "output_tokens", 0) or 0),
        reasoning_tokens=int(getattr(out, "reasoning_tokens", 0) or 0),
    )


def google_usage(response: Any) -> Usage:
    raw = getattr(response, "usage_metadata", None)
    prompt = int(getattr(raw, "prompt_token_count", 0) or 0)
    cached = int(getattr(raw, "cached_content_token_count", 0) or 0)
    visible = int(getattr(raw, "candidates_token_count", 0) or 0)
    thoughts = int(getattr(raw, "thoughts_token_count", 0) or 0)
    return Usage(
        input_tokens=prompt,
        cached_input_tokens=cached,
        output_tokens=visible + thoughts,
        reasoning_tokens=thoughts,
    )


def call_openai(client: Any, candidate: dict, system: str, user: str, max_tokens: int) -> ProviderEnvelope:
    schema = EvaluatorRating.model_json_schema(by_alias=True)
    response = client.responses.create(
        model=candidate["model"],
        input=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        max_output_tokens=max_tokens,
        text={
            "format": {
                "type": "json_schema",
                "name": "study_e_evaluator_rating",
                "strict": True,
                "schema": schema,
            }
        },
        store=False,
    )
    return ProviderEnvelope(
        raw_text=(getattr(response, "output_text", "") or "").strip(),
        provider_response=jsonable_response(response),
        usage=openai_usage(response),
        stop_reason=str(getattr(response, "status", "") or "") or None,
        response_id=str(getattr(response, "id", "") or "") or None,
    )


def call_anthropic(client: Any, candidate: dict, system: str, user: str, max_tokens: int) -> ProviderEnvelope:
    from anthropic import transform_schema

    response = client.messages.create(
        model=candidate["model"],
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
        output_config={
            "format": {
                "type": "json_schema",
                "schema": transform_schema(EvaluatorRating),
            }
        },
    )
    raw_text = "".join(
        block.text for block in getattr(response, "content", [])
        if getattr(block, "type", None) == "text"
    ).strip()
    return ProviderEnvelope(
        raw_text=raw_text,
        provider_response=jsonable_response(response),
        usage=anthropic_usage(response),
        stop_reason=str(getattr(response, "stop_reason", "") or "") or None,
        response_id=str(getattr(response, "id", "") or "") or None,
    )


def call_google(client: Any, candidate: dict, system: str, user: str, max_tokens: int) -> ProviderEnvelope:
    from google.genai import types

    config = types.GenerateContentConfig(
        system_instruction=system,
        max_output_tokens=max_tokens,
        response_mime_type="application/json",
        response_json_schema=google_json_schema(EvaluatorRating),
    )
    response = client.models.generate_content(
        model=candidate["model"],
        contents=user,
        config=config,
    )
    candidates = getattr(response, "candidates", None) or []
    stop = str(getattr(candidates[0], "finish_reason", "") or "") if candidates else ""
    return ProviderEnvelope(
        raw_text=(getattr(response, "text", "") or "").strip(),
        provider_response=jsonable_response(response),
        usage=google_usage(response),
        stop_reason=stop or None,
        response_id=str(getattr(response, "response_id", "") or "") or None,
    )


def is_retryable(exc: Exception, allowed_statuses: set[int]) -> bool:
    status = getattr(exc, "status_code", None)
    if not isinstance(status, int):
        status = getattr(exc, "code", None)
    if isinstance(status, int):
        return status in allowed_statuses
    return type(exc).__name__ in {
        "APIConnectionError",
        "APITimeoutError",
        "TimeoutError",
        "ConnectionError",
    }


def calculate_cost(candidate: dict, usage: Usage) -> float:
    rates = candidate["rates_per_million_tokens"]
    uncached = max(0, usage.input_tokens - usage.cached_input_tokens - usage.cache_write_input_tokens)
    value = (
        uncached * rates["input"]
        + usage.cached_input_tokens * rates.get("cached_input", rates["input"])
        + usage.cache_write_input_tokens * rates.get("cache_write_input", rates["input"])
        + usage.output_tokens * rates["output"]
    ) / 1_000_000
    return round(value, 8)


def result_path(candidate_id: str, item_id: str, directory: Path = RESULTS_DIR) -> Path:
    return directory / f"{candidate_id}__{item_id}.json"


def create_clients(config: dict) -> dict[str, Any]:
    load_environment()
    required = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "google": "GOOGLE_API_KEY",
    }
    missing = [variable for provider, variable in required.items() if not os.getenv(variable)]
    if missing:
        raise RuntimeError(f"missing API key environment variables: {', '.join(missing)}")
    from anthropic import Anthropic
    from google import genai
    from openai import OpenAI

    timeout = float(config["execution"]["request_timeout_seconds"])
    return {
        "openai": OpenAI(max_retries=0, timeout=timeout),
        "anthropic": Anthropic(max_retries=0, timeout=timeout),
        "google": genai.Client(api_key=os.environ["GOOGLE_API_KEY"]),
    }


def account_access_check() -> dict:
    config = load_config()
    clients = create_clients(config)
    results = []
    for candidate in config["candidates"]:
        provider = candidate["provider"]
        requested = candidate["model"]
        try:
            if provider == "openai":
                response = clients[provider].models.retrieve(requested)
                returned = str(getattr(response, "id", "") or "")
            elif provider == "anthropic":
                response = clients[provider].models.retrieve(requested)
                returned = str(getattr(response, "id", "") or "")
            elif provider == "google":
                response = clients[provider].models.get(model=requested)
                returned = str(getattr(response, "name", "") or "")
            else:
                raise ValueError(f"unsupported provider: {provider}")
            accessible = returned == requested or returned.endswith("/" + requested)
            results.append(
                {
                    "candidate_id": candidate["candidate_id"],
                    "provider": provider,
                    "requested_model": requested,
                    "returned_model": returned,
                    "accessible": accessible,
                    "error_kind": None,
                    "error_message": None,
                }
            )
        except Exception as exc:
            results.append(
                {
                    "candidate_id": candidate["candidate_id"],
                    "provider": provider,
                    "requested_model": requested,
                    "returned_model": None,
                    "accessible": False,
                    "error_kind": type(exc).__name__,
                    "error_message": str(exc)[:1000],
                }
            )
    receipt = {
        "schema_version": "study-e-evaluator-account-access-v1",
        "checked_at": utc_now(),
        "check_type": "model metadata lookup only; no generation request",
        "results": results,
        "all_accessible": all(result["accessible"] for result in results),
        "generation_calls": 0,
        "token_cost_usd": 0.0,
    }
    write_terminal(ACCESS_RECEIPT_PATH, receipt)
    return receipt


def invoke(provider: str, client: Any, candidate: dict, system: str, user: str, max_tokens: int) -> ProviderEnvelope:
    if provider == "openai":
        return call_openai(client, candidate, system, user, max_tokens)
    if provider == "anthropic":
        return call_anthropic(client, candidate, system, user, max_tokens)
    if provider == "google":
        return call_google(client, candidate, system, user, max_tokens)
    raise ValueError(f"unsupported provider: {provider}")


def execute_pair(
    *,
    row: dict,
    candidate: dict,
    item: dict,
    common: str,
    system: str,
    template: str,
    config: dict,
    client: Any,
    output_directory: Path = RESULTS_DIR,
) -> dict:
    user = build_user_prompt(template, common, item)
    allowed = set(config["execution"]["retryable_statuses"])
    total_attempts = int(config["execution"]["transport_retries_after_first_attempt"]) + 1
    max_tokens = int(config["execution"]["max_output_tokens"])
    attempts = []
    terminal_status = "transport_failure"
    rating = None
    for attempt_number in range(1, total_attempts + 1):
        started = time.perf_counter()
        started_at = utc_now()
        envelope = None
        try:
            envelope = invoke(row["provider"], client, candidate, system, user, max_tokens)
            latency_ms = round((time.perf_counter() - started) * 1000)
            validation_error_locations = []
            try:
                if not envelope.raw_text:
                    raise ValueError("provider returned no structured text")
                parsed = EvaluatorRating.model_validate_json(envelope.raw_text)
                if parsed.item_id != item["item_id"]:
                    raise ValueError("model returned a mismatched item_id")
                rating = parsed.model_dump(mode="json", by_alias=True)
                terminal_status = "success"
                error_kind = None
                error_message = None
            except (ValidationError, ValueError, json.JSONDecodeError) as exc:
                terminal_status = "schema_failure"
                error_kind = type(exc).__name__
                error_message = str(exc)[:2000]
                if isinstance(exc, ValidationError):
                    validation_error_locations = [list(e["loc"]) for e in exc.errors()]
            cost = calculate_cost(candidate, envelope.usage)
            attempts.append(
                {
                    "attempt": attempt_number,
                    "started_at": started_at,
                    "latency_ms": latency_ms,
                    "status": terminal_status,
                    "usage": envelope.usage.model_dump(mode="json"),
                    "cost_usd": cost,
                    "stop_reason": envelope.stop_reason,
                    "response_id": envelope.response_id,
                    "validation_error_locations": validation_error_locations,
                    "raw_text": envelope.raw_text,
                    "raw_text_sha256": sha256_bytes(envelope.raw_text.encode("utf-8")),
                    "provider_response": envelope.provider_response,
                    "error_kind": error_kind,
                    "error_message": error_message,
                }
            )
            break
        except Exception as exc:
            latency_ms = round((time.perf_counter() - started) * 1000)
            attempts.append(
                {
                    "attempt": attempt_number,
                    "started_at": started_at,
                    "latency_ms": latency_ms,
                    "status": "transport_error",
                    "usage": Usage().model_dump(mode="json"),
                    "cost_usd": 0.0,
                    "stop_reason": None,
                    "response_id": None,
                    "raw_text": None,
                    "raw_text_sha256": None,
                    "provider_response": None,
                    "error_kind": type(exc).__name__,
                    "error_message": str(exc)[:2000],
                }
            )
            if not is_retryable(exc, allowed) or attempt_number == total_attempts:
                terminal_status = "transport_failure"
                break
            time.sleep(min(8, 2 ** (attempt_number - 1)))
    record = {
        "schema_version": "study-e-evaluator-terminal-record-v1",
        "schedule_index": row["schedule_index"],
        "candidate_id": row["candidate_id"],
        "provider": row["provider"],
        "model": row["model"],
        "item_id": row["item_id"],
        "terminal_status": terminal_status,
        "rating": rating,
        "attempts": attempts,
        "total_cost_usd": round(sum(attempt["cost_usd"] for attempt in attempts), 8),
        "prompt_sha256": sha256_bytes((system + "\n\n" + user).encode("utf-8")),
        "freeze_manifest_sha256": sha256_file(FREEZE_PATH),
    }
    write_terminal(result_path(row["candidate_id"], row["item_id"], output_directory), record)
    return record


def existing_records(directory: Path = RESULTS_DIR) -> list[dict]:
    if not directory.exists():
        return []
    records = []
    for path in sorted(directory.glob("*.json")):
        records.append(json.loads(path.read_text(encoding="utf-8")))
    return records


def spent_cost(records: list[dict]) -> float:
    return round(sum(float(record.get("total_cost_usd", 0)) for record in records), 8)


def projected_call_cost(candidate: dict, system: str, user: str, max_tokens: int) -> float:
    usage = Usage(input_tokens=len(system) + len(user), output_tokens=max_tokens)
    return calculate_cost(candidate, usage)


def paid_run(confirmation: str) -> None:
    manifest = verify_freeze()
    config = load_config()
    required = config["execution"]["paid_confirmation_phrase"]
    if confirmation != required:
        raise RuntimeError(f"paid run requires --confirm {required}")
    inputs = json.loads(INPUT_PATH.read_text(encoding="utf-8"))
    schedule = json.loads(SCHEDULE_PATH.read_text(encoding="utf-8"))["rows"]
    system, template = parse_prompt()
    by_candidate = {candidate["candidate_id"]: candidate for candidate in config["candidates"]}
    by_item = {item["item_id"]: item for item in inputs["items"]}
    clients = create_clients(config)
    records = existing_records()
    smoke_cost = json.loads((PRIVATE / "v3" / "smoke.json").read_text(encoding="utf-8"))["total_cost_usd"]
    existing_keys = {(record["candidate_id"], record["item_id"]) for record in records}
    if len(existing_keys) != len(records):
        raise RuntimeError("duplicate terminal result keys found")
    cap = float(config["execution"]["max_total_cost_usd"])
    for row in schedule:
        key = (row["candidate_id"], row["item_id"])
        if key in existing_keys:
            continue
        candidate = by_candidate[row["candidate_id"]]
        item = by_item[row["item_id"]]
        user = build_user_prompt(template, inputs["common_evidence"], item)
        projected = projected_call_cost(
            candidate, system, user, int(config["execution"]["max_output_tokens"])
        )
        current = spent_cost(records) + smoke_cost + 0.33626710
        if current + projected * 3 > cap:
            raise CostCapError(
                f"projected next call would exceed cost cap: {current:.6f} + {projected:.6f} > {cap:.2f}"
            )
        record = execute_pair(
            row=row,
            candidate=candidate,
            item=item,
            common=inputs["common_evidence"],
            system=system,
            template=template,
            config=config,
            client=clients[row["provider"]],
        )
        records.append(record)
        if record["terminal_status"] == "transport_failure":
            raise RuntimeError("Request/connection failure: stopped for diagnosis; terminal record preserved.")
        if record["terminal_status"] == "schema_failure" and ["schema_version"] in record["attempts"][-1].get("validation_error_locations", []):
            raise RuntimeError("Version contract failure: stopped for diagnosis; terminal record preserved.")
        existing_keys.add(key)
        print(
            f"completed={len(records)}/{manifest['planned_assessments']} "
            f"schedule_index={row['schedule_index']} status={record['terminal_status']} "
            f"cumulative_cost_usd={spent_cost(records):.6f}",
            flush=True,
        )
    print(
        f"run_complete terminal_records={len(records)} total_cost_usd={spent_cost(records):.6f}; "
        "model judgments were not printed",
        flush=True,
    )


def dependency_status() -> dict:
    packages = ["openai", "anthropic", "google-genai", "pydantic", "python-dotenv"]
    observed = {}
    for package in packages:
        try:
            observed[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            observed[package] = None
    return observed


def preflight() -> dict:
    manifest = verify_freeze()
    config = load_config()
    load_environment()
    expected = config["sdk_versions"]
    observed = dependency_status()
    version_ok = (
        platform.python_version() == expected["python"]
        and all(observed[name] == expected[name] for name in observed)
    )
    keys = {
        variable: bool(os.getenv(variable))
        for variable in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY")
    }
    records = existing_records()
    result = {
        "freeze_verified": True,
        "planned_assessments": manifest["planned_assessments"],
        "existing_terminal_records": len(records),
        "sdk_versions_match": version_ok,
        "observed_sdk_versions": observed,
        "python_version": platform.python_version(),
        "api_keys_present": keys,
        "account_access_receipt_all_accessible": json.loads(
            ACCESS_RECEIPT_PATH.read_text(encoding="utf-8")
        )["all_accessible"],
        "paid_calls_made_by_preflight": 0,
    }
    if not version_ok:
        raise RuntimeError(f"SDK version mismatch: {result}")
    return result


def fake_rating(item_id: str) -> EvaluatorRating:
    return EvaluatorRating.model_validate(
        {
            "schema_version": "study-e-evaluator-rating-v1",
            "item_id": item_id,
            "scores": {
                "persona_fit": 4,
                "clarity": 4,
                "actionability": 4,
                "factual_grounding": 4,
            },
            "reasons": {
                "persona_fit": "Synthetic dry-run reason.",
                "clarity": "Synthetic dry-run reason.",
                "actionability": "Synthetic dry-run reason.",
                "factual_grounding": "Synthetic dry-run reason.",
            },
            "critical_violation": False,
            "critical_violation_type": None,
            "critical_evidence_quote": None,
            "total_score": 16,
            "pass": True,
            "low_quality": False,
        }
    )


def dry_run() -> dict:
    verify_freeze()
    config = load_config()
    inputs = json.loads(INPUT_PATH.read_text(encoding="utf-8"))
    schedule = json.loads(SCHEDULE_PATH.read_text(encoding="utf-8"))["rows"]
    system, template = parse_prompt()
    by_candidate = {candidate["candidate_id"]: candidate for candidate in config["candidates"]}
    by_item = {item["item_id"]: item for item in inputs["items"]}
    with tempfile.TemporaryDirectory(prefix="study-e-evaluator-dry-") as temporary:
        directory = Path(temporary)
        for row in schedule:
            item = by_item[row["item_id"]]
            user = build_user_prompt(template, inputs["common_evidence"], item)
            parsed = fake_rating(item["item_id"])
            record = {
                "schema_version": "study-e-evaluator-terminal-record-v1",
                "schedule_index": row["schedule_index"],
                "candidate_id": row["candidate_id"],
                "provider": row["provider"],
                "model": row["model"],
                "item_id": row["item_id"],
                "terminal_status": "success",
                "rating": parsed.model_dump(mode="json", by_alias=True),
                "attempts": [],
                "total_cost_usd": 0.0,
                "prompt_sha256": sha256_bytes((system + "\n\n" + user).encode("utf-8")),
                "freeze_manifest_sha256": sha256_file(FREEZE_PATH),
            }
            write_terminal(result_path(row["candidate_id"], row["item_id"], directory), record)
        records = existing_records(directory)
        keys = {(record["candidate_id"], record["item_id"]) for record in records}
        result = {
            "terminal_records": len(records),
            "unique_candidate_item_pairs": len(keys),
            "valid_ratings": sum(
                EvaluatorRating.model_validate(record["rating"]) is not None for record in records
            ),
            "provider_counts": {
                candidate["provider"]: sum(record["provider"] == candidate["provider"] for record in records)
                for candidate in config["candidates"]
            },
            "paid_calls": 0,
        }
    if result["terminal_records"] != config["execution"]["planned_assessments"]:
        raise RuntimeError(f"dry run failed: {result}")
    return result


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Freeze, validate, and run Study E evaluator selection")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("freeze")
    subparsers.add_parser("access-check")
    subparsers.add_parser("preflight")
    subparsers.add_parser("dry-run")
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--confirm", default="")
    args = parser.parse_args()
    if args.command == "access-check":
        result = account_access_check()
    elif args.command == "freeze":
        result = freeze()
    elif args.command == "preflight":
        result = preflight()
    elif args.command == "dry-run":
        result = dry_run()
    else:
        paid_run(args.confirm)
        return
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
