"""Manual Langfuse v3 telemetry for the NEW final runner only.

Call ``healthcheck()`` before constructing paid clients. Save the authoritative
local attempt result BEFORE ``handle.finish(row)``. Telemetry failures never
become model failures or cause model retries. This module does not load .env,
instantiate a client at import/construction, or make model calls.

SDK: langfuse==3.6.1, opentelemetry-api/sdk==1.44.0. Trace IDs and logical task /
attempt IDs are deterministic; Langfuse's supported API assigns observation IDs.
The actual observation ID is returned in the receipt for ledger correlation.
Cloud costs may be inferred by Langfuse; local known-cost accounting remains the
research authority. Unknown reservations are NEVER exported as known costs.

Official API references checked 2026-09-06:
https://langfuse.com/docs/observability/sdk/instrumentation
https://langfuse.com/docs/observability/features/token-and-cost-tracking
https://langfuse.com/docs/observability/features/trace-ids-and-distributed-tracing
"""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
import hashlib
import json
import math
import os
import re
import threading
from typing import Any, Callable
try:
    from .pricing import usage_details
except ImportError:
    from pricing import usage_details


class TelemetryUnavailable(RuntimeError):
    """Preflight failure: no paid request may start."""


def _id(kind: str, *parts: str, size: int = 32) -> str:
    raw = json.dumps(["STUDY-E-ABLATON", kind, *parts], ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:size]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class AttemptHandle:
    def __init__(self, owner, observation, metadata):
        self.owner = owner
        self.observation = observation
        self.metadata = metadata
        self.finished = False
        self.receipt = {**metadata, "observation_id": getattr(observation, "id", None),
                        "export_enqueued": False, "delivery_verified": False}

    def finish(self, row: dict) -> dict:
        """Best-effort update, called once AFTER the local result was saved."""
        if self.finished:
            return dict(self.receipt)
        self.finished = True
        try:
            status = self.owner.safe_label(row.get("status", "unknown"))
            cost = row.get("cost_usd")
            known = type(cost) in (int, float) and math.isfinite(cost) and cost >= 0
            metadata = {**self.metadata, "local_status": status,
                        "cost_status": "known_usage_cost" if known else "unknown",
                        "local_usage": self.owner.sanitize(row.get("usage")),
                        "latency_ms": row.get("latency_ms"),
                        "freeze_sha256": row.get("freeze_sha256"),
                        "actual_model": (row.get("provider_response") or {}).get(
                            "model", (row.get("provider_response") or {}).get("model_version"))}
            for field in ("error_kind", "error_code", "http_status", "stop_reason", "pricing_error_kind",
                          "pricing_sha256", "pricing_verified_date", "actual_service_tier"):
                if row.get(field) is not None:
                    metadata[field] = self.owner.safe_label(row[field])
            if row.get('validation_detail') is not None:
                metadata['validation_detail'] = self.owner.sanitize(str(row['validation_detail'])[:800])
            # Arbitrary error bodies/messages/tracebacks are deliberately excluded.
            output = row.get("output")
            if output is None and row.get("raw_text") is not None:
                output = {"unparsed_model_output": row["raw_text"]}
            update = {"output": self.owner.sanitize(output),
                      "metadata": self.owner.sanitize(metadata),
                      "level": "DEFAULT" if status == "success" else "ERROR",
                      "status_message": status}
            # Unverified usage stays in metadata; Cloud must not infer its cost.
            tokens = usage_details(row.get("usage")) if known else None
            if tokens is not None:
                update["usage_details"] = tokens
            if known:
                details = row.get('cost_details')
                if details is not None:
                    if any(type(v) not in (int,float) or not math.isfinite(v) or v<0 for v in details.values()):
                        raise ValueError('invalid_cost_breakdown')
                    if not math.isclose(details.get('total',-1),cost,rel_tol=0,abs_tol=1e-8):
                        raise ValueError('cost_total_mismatch')
                    if not math.isclose(sum(v for k,v in details.items() if k!='total'),cost,rel_tol=0,abs_tol=1e-8):
                        raise ValueError('cost_components_mismatch')
                update["cost_details"] = dict(details) if details is not None else {"total": float(cost)}
            if self.observation is not None:
                self.observation.update(**update)
                self.receipt["export_enqueued"] = True
            self.receipt.update(local_status=status, cost_status=metadata["cost_status"])
        except Exception as exc:
            self.owner._failure("attempt_finish", exc, self.metadata)
        self.owner._record(self.receipt)
        return dict(self.receipt)


class Telemetry:
    def __init__(self, session_id: str, enabled: bool = True, *, client=None,
                 failure_sink: Callable[[dict], None] | None = None):
        if not isinstance(session_id, str) or not session_id:
            raise ValueError("session_id_required")
        self.session_id = session_id
        self.enabled = bool(enabled)
        self.client = client  # Injected clients are for offline tests only.
        self._injected_client = client is not None
        self._ready = False
        self._failure_sink = failure_sink
        self._lock = threading.RLock()
        self._task = ContextVar("study_e_telemetry_task_" + _id("session", session_id), default=None)
        self.errors: list[dict] = []
        self.records: list[dict] = []
        self._secrets = tuple(v for k, v in os.environ.items()
                              if re.search(r"KEY|SECRET|TOKEN|PASSWORD", k, re.I) and len(v) >= 8)

    def safe_label(self, value: Any) -> str:
        value = self.sanitize(str(value))
        return re.sub(r"[^A-Za-z0-9_.:\-]", "_", value)[:120]

    def sanitize(self, value: Any) -> Any:
        """Retain research text, remove credential fields and known secret values."""
        if isinstance(value, dict):
            clean = {}
            for key, item in value.items():
                name = str(key)
                sensitive = re.search(r"api[_-]?key|secret|authorization|password|"
                                      r"access[_-]?token|refresh[_-]?token|cookie|headers", name, re.I)
                clean[name] = "[REDACTED]" if sensitive else self.sanitize(item)
            return clean
        if isinstance(value, (list, tuple)):
            return [self.sanitize(item) for item in value]
        if isinstance(value, str):
            for secret in self._secrets:
                value = value.replace(secret, "[REDACTED]")
            return re.sub(r"\b(?:sk|pk)-(?:lf-|ant-)?[A-Za-z0-9_-]{12,}", "[REDACTED]", value)
        if value is None or type(value) in (bool, int):
            return value
        if isinstance(value, float):
            return value if math.isfinite(value) else None
        if hasattr(value, "model_dump"):
            return self.sanitize(value.model_dump(mode="json"))
        return {"unserialized_type": type(value).__name__}

    def _mask(self, data: Any, **_kwargs) -> Any:
        # Langfuse 3.6.1 invokes the callback as mask(data=...), not positionally.
        return self.sanitize(data)

    def _record(self, value: dict):
        with self._lock:
            self.records.append(dict(value))

    def _failure(self, stage: str, exc: BaseException, metadata: dict | None = None):
        # No str(exc): providers/HTTP exporters can embed credentials in messages.
        row = {"created_at": _now(), "stage": stage, "error_kind": type(exc).__name__,
               "session_id": self.session_id,
               "task_id": (metadata or {}).get("task_id"),
               "attempt_key": (metadata or {}).get("attempt_key"),
               "requires_ledger_reconciliation": True}
        with self._lock:
            self.errors.append(row)
        if self._failure_sink:
            try:
                self._failure_sink(dict(row))
            except Exception as sink_exc:
                with self._lock:
                    self.errors.append({**row, "stage": "failure_sink",
                                        "error_kind": type(sink_exc).__name__})

    def healthcheck(self) -> dict:
        """Check credentials/endpoint once, without any model call or trace upload.

        auth_check is a read-only Langfuse request. Success is not an ingestion
        delivery acknowledgement. Do not invoke this live method in offline prep.
        """
        if not self.enabled:
            return {"ok": True, "mode": "offline_disabled", "ready_for_paid_calls": False}
        if not self._ready:
            try:
                if self.client is None:
                    self._secrets = tuple(v for k, v in os.environ.items()
                        if re.search(r"KEY|SECRET|TOKEN|PASSWORD", k, re.I) and len(v) >= 8)
                    names = ("LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY")
                    if any(not os.getenv(name) for name in names):
                        raise TelemetryUnavailable("missing_LANGFUSE_credentials")
                    host = os.getenv("LANGFUSE_HOST") or os.getenv("LANGFUSE_BASE_URL")
                    if not host:
                        raise TelemetryUnavailable("missing_LANGFUSE_HOST_or_BASE_URL")
                    if os.getenv("LANGFUSE_TRACING_ENABLED", "true").lower() in ("0", "false", "no"):
                        raise TelemetryUnavailable("LANGFUSE_tracing_disabled")
                    if os.getenv("OTEL_SDK_DISABLED", "false").lower() in ("1", "true", "yes"):
                        raise TelemetryUnavailable("OpenTelemetry_disabled")
                    from langfuse import Langfuse
                    self.client = Langfuse(public_key=os.environ[names[0]],
                        secret_key=os.environ[names[1]], host=host, timeout=15,
                        debug=False, tracing_enabled=True, sample_rate=1.0, mask=self._mask)
                if self.client.auth_check() is not True:
                    raise TelemetryUnavailable("LANGFUSE_auth_check_failed")
                self._ready = True
            except Exception as exc:
                self._failure("healthcheck", exc)
                raise TelemetryUnavailable("LANGFUSE_preflight_failed_" + type(exc).__name__) from None
        return {"ok": True, "mode": "injected_offline_client" if self._injected_client else "live",
                "ready_for_paid_calls": not self._injected_client,
                "auth_checked": True, "delivery_verified": False}

    def _require_ready(self):
        if self.enabled and not self._ready:
            raise TelemetryUnavailable("call_healthcheck_before_paid_requests")

    def _close(self, cm, metadata):
        if cm is not None:
            try:
                # Do not pass application exceptions into SDK automatic exception logging.
                cm.__exit__(None, None, None)
            except Exception as exc:
                self._failure("observation_close", exc, metadata)

    @contextmanager
    def task(self, task_id: str, metadata: dict | None = None):
        self._require_ready()
        info = {**(metadata or {}), "study_id": "STUDY-E-ABLATON",
                "session_id": self.session_id, "task_id": task_id,
                "logical_task_id": _id("task", self.session_id, task_id),
                "trace_id": _id("trace", self.session_id, task_id)}
        token = self._task.set(info)
        cm = observation = None
        if self.enabled:
            try:
                cm = self.client.start_as_current_observation(as_type="span",
                    name="STUDY-E-ABLATON-task", trace_context={"trace_id": info["trace_id"]},
                    input={"task_id": task_id}, metadata=self.sanitize(info))
                observation = cm.__enter__()
                observation.update_trace(session_id=self.session_id, name="STUDY-E-ABLATON-task",
                                         metadata=self.sanitize(info))
            except Exception as exc:
                self._failure("task_start", exc, info)
        try:
            yield {**info, "observation_id": getattr(observation, "id", None)}
        except BaseException as exc:
            if observation is not None:
                try:
                    observation.update(level="ERROR", status_message=type(exc).__name__)
                except Exception as update_exc:
                    self._failure("task_error_update", update_exc, info)
            raise
        finally:
            self._close(cm, info)
            self._task.reset(token)

    @contextmanager
    def attempt(self, key: str, role: str, payload: dict, candidate: dict,
                request: dict, metadata: dict | None = None):
        self._require_ready()
        task = self._task.get()
        if task is None:
            raise TelemetryUnavailable("attempt_requires_task_context")
        info = {**task, **(metadata or {}), "attempt_key": key, "role": role,
                "logical_attempt_id": _id("attempt", self.session_id, task["task_id"], key),
                "model_provider": candidate.get("provider")}
        cm = observation = None
        if self.enabled:
            try:
                parameters = {k: request[k] for k in ("max_tokens", "max_output_tokens", "temperature", "service_tier",
                    "top_p", "seed", "reasoning", "thinking", "output_config", "config") if k in request}
                # v3 model_parameters values must be scalar/list[str]; preserve complex config as JSON.
                parameters = {k: json.dumps(self.sanitize(v), ensure_ascii=False, sort_keys=True)
                              if isinstance(v, dict) or hasattr(v, "model_dump") else v
                              for k, v in parameters.items()}
                cm = self.client.start_as_current_observation(as_type="generation",
                    name="STUDY-E-ABLATON-" + role, model=candidate.get("model"),
                    input=self.sanitize({"payload": payload, "request": request}),
                    model_parameters=parameters, metadata=self.sanitize(info))
                observation = cm.__enter__()
            except Exception as exc:
                self._failure("attempt_start", exc, info)
        handle = AttemptHandle(self, observation, info)
        try:
            yield handle
        except BaseException as exc:
            if not handle.finished:
                handle.finish({"status": "application_exception", "error_kind": type(exc).__name__})
            raise
        finally:
            if not handle.finished:
                self._failure("attempt_missing_local_result", RuntimeError(), info)
            self._close(cm, info)

    def flush(self) -> dict:
        if self.enabled and self.client is not None:
            try:
                self.client.flush()
            except Exception as exc:
                self._failure("flush", exc)
        return self.receipt()

    def receipt(self) -> dict:
        with self._lock:
            return {"schema_version": "STUDY-E-ABLATON-telemetry-v1", "session_id": self.session_id,
                    "enabled": self.enabled, "auth_checked": self._ready,
                    "delivery_verified": False, "errors": list(self.errors),
                    "attempts": list(self.records),
                    "status": "DEGRADED" if self.errors else ("READY" if self._ready else "OFFLINE")}

    def replay_attempt(self, start: dict, row: dict, *, task_id: str, metadata: dict | None = None) -> dict:
        """Explicitly export a saved local attempt; NEVER call a model.

        Replay keeps the deterministic logical IDs, but SDK-assigned observation
        IDs differ. It is not cloud-idempotent: reconcile by logical_attempt_id
        and mark duplicates rather than summing them. Span time is replay time;
        original timestamps/latency stay in metadata. No automatic replay occurs.
        """
        info = {**(metadata or {}), "ledger_replay": True,
                "original_created_at": start.get("created_at"),
                "original_latency_ms": row.get("latency_ms"),
                "request_sha256": start.get("request_sha256"),
                "parent_sha256": start.get("parent_sha256"),
                "freeze_sha256": start.get("freeze_sha256")}
        with self.task(task_id, info):
            with self.attempt(start["key"], start["role"], start["payload"],
                              start["candidate"], start["request"], info) as handle:
                return handle.finish(row)
