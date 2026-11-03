"""Offline-only telemetry tests: injected client, no SDK exports/model calls."""
from contextlib import contextmanager
import importlib.util
import json
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("final_telemetry_tested", Path(__file__).with_name("telemetry.py"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
Telemetry, TelemetryUnavailable = mod.Telemetry, mod.TelemetryUnavailable


class Observation:
    def __init__(self, number, fail_update=False):
        self.id = f"{number:016x}"
        self.updates = []
        self.traces = []
        self.fail_update = fail_update

    def update(self, **kwargs):
        if self.fail_update:
            raise RuntimeError("fake secret exception must never be logged")
        self.updates.append(kwargs)

    def update_trace(self, **kwargs):
        self.traces.append(kwargs)


class FakeClient:
    def __init__(self, *, auth=True, fail=None):
        self.auth = auth
        self.fail = fail
        self.calls = []
        self.auth_calls = 0
        self.flush_calls = 0
        self.closed = 0

    def auth_check(self):
        self.auth_calls += 1
        if self.fail == "auth":
            raise RuntimeError("do not expose secret")
        return self.auth

    @contextmanager
    def start_as_current_observation(self, **kwargs):
        if self.fail == "start":
            raise RuntimeError("fake secret exception must never be logged")
        obs = Observation(len(self.calls) + 1, self.fail == "update")
        self.calls.append((kwargs, obs))
        try:
            yield obs
        finally:
            self.closed += 1
            if self.fail == "close":
                raise RuntimeError("fake secret exception must never be logged")

    def flush(self):
        self.flush_calls += 1
        if self.fail == "flush":
            raise RuntimeError("fake secret exception must never be logged")


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    import socket
    def forbidden(*args, **kwargs):
        raise AssertionError("Network is forbidden in offline telemetry tests")
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)


def make(client=None, **kwargs):
    client = client or FakeClient()
    tel = Telemetry("final-natural-125", client=client, **kwargs)
    assert tel.healthcheck()["mode"] == "injected_offline_client"
    return tel, client


def row():
    return {"status": "success", "output": {"body": "a preserved result"},
            "usage": {"input_tokens": 100, "cached_input_tokens": 20,
                      "cache_write_input_tokens": 10, "output_tokens": 40, "reasoning_tokens": 5},
            "cost_usd": 0.012, "budget_charge_usd": 100,
            "provider_response": {"model": "frozen-model-2026-09-06"}, "latency_ms": 250}


def attempt(tel, key="T001_writer__a01"):
    return tel.attempt(key, "writer", {"brief": "test"}, {"provider": "openai", "model": "frozen-model"},
                       {"max_output_tokens": 2048, "reasoning": {"effort": "none"}},
                       {"local_result_path": "results/" + key + ".json"})


def test_constructor_is_offline_and_live_gate_requires_healthcheck(monkeypatch):
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    tel = Telemetry("no-side-effects")
    assert tel.client is None
    with pytest.raises(TelemetryUnavailable, match="healthcheck"):
        with tel.task("T001"):
            pytest.fail("Cannot reach a paid operation")
    with pytest.raises(TelemetryUnavailable, match="preflight"):
        tel.healthcheck()


def test_healthcheck_false_and_exception_block_paid_calls():
    for client in (FakeClient(auth=False), FakeClient(fail="auth")):
        tel = Telemetry("s", client=client)
        with pytest.raises(TelemetryUnavailable):
            tel.healthcheck()
        assert not tel.receipt()["auth_checked"]
        assert "secret" not in json.dumps(tel.errors)


def test_success_span_generation_usage_cost_and_local_link():
    tel, client = make()
    saved_locally = []
    with tel.task("T001", {"batch_id": 1}):
        with attempt(tel) as handle:
            saved_locally.append(row())
            receipt = handle.finish(saved_locally[-1])
            assert handle.finish(row()) == receipt  # No duplicate telemetry update.
    assert len(saved_locally) == 1
    assert [c[0]["as_type"] for c in client.calls] == ["span", "generation"]
    gen_args, gen = client.calls[1]
    assert len(gen.updates) == 1
    assert gen.updates[0]["usage_details"] == {"input": 70, "cache_read_input_tokens": 20,
        "cache_creation_input_tokens": 10, "output": 35, "reasoning_output_tokens": 5, "total": 140}
    assert gen.updates[0]["cost_details"] == {"total": 0.012}
    assert gen_args["model_parameters"]["reasoning"] == '{"effort": "none"}'
    assert receipt["local_result_path"].endswith("__a01.json")
    assert receipt["observation_id"] == gen.id
    assert receipt["export_enqueued"] and not receipt["delivery_verified"]
    assert client.closed == 2


def test_google_usage_excludes_cache_and_thought_double_count():
    usage = mod.usage_details({"prompt_token_count": 100, "cached_content_token_count": 20,
                              "candidates_token_count": 10, "thoughts_token_count": 50,
                              "total_token_count": 160})
    assert usage == {"input": 80, "cache_read_input_tokens": 20, "output": 10,
                     "reasoning_output_tokens": 50, "total": 160}


def test_unknown_cost_never_exports_reservation_as_actual_or_zero():
    tel, client = make()
    data = {**row(), "status": "transport_failure", "usage": None,
            "cost_usd": None, "budget_charge_usd": 123.45, "error_body": "secret"}
    with tel.task("T001"):
        with attempt(tel) as handle:
            handle.finish(data)
    update = client.calls[1][1].updates[0]
    assert "cost_details" not in update and "usage_details" not in update
    assert update["metadata"]["cost_status"] == "unknown"
    assert "123.45" not in json.dumps(update) and "error_body" not in json.dumps(update)


@pytest.mark.parametrize("failure", ["start", "update", "close", "flush"])
def test_telemetry_failure_does_not_repeat_or_erase_paid_result(failure):
    tel, _ = make(FakeClient(fail=failure))
    local_results = []
    with tel.task("T001"):
        with attempt(tel) as handle:
            local_results.append(row())  # Exactly one simulated paid call/local write.
            handle.finish(local_results[-1])
    tel.flush()
    assert len(local_results) == 1 and local_results[0]["status"] == "success"
    assert tel.errors and "fake secret" not in json.dumps(tel.receipt())


def test_application_exception_is_not_swallowed_or_sent_to_sdk():
    tel, client = make()
    with pytest.raises(ValueError, match="application-secret"):
        with tel.task("T001"):
            with attempt(tel):
                raise ValueError("application-secret")
    assert "application-secret" not in json.dumps(tel.receipt())
    assert "application-secret" not in json.dumps([c[1].updates for c in client.calls])
    assert client.closed == 2


def test_ids_are_deterministic_but_distinguish_sessions_tasks_attempts():
    ids = []
    for session in ("same", "same", "other"):
        tel, _ = make()  # Then create explicit session, retaining injected fake client.
        tel = Telemetry(session, client=FakeClient()); tel.healthcheck()
        with tel.task("T001") as task_info:
            with attempt(tel) as handle:
                result = handle.finish(row())
        ids.append((task_info["trace_id"], result["logical_attempt_id"]))
    assert ids[0] == ids[1] and ids[0] != ids[2]
    assert len(ids[0][0]) == 32


def test_disabled_is_explicitly_offline_not_paid_ready():
    tel = Telemetry("offline", enabled=False)
    assert tel.healthcheck()["ready_for_paid_calls"] is False
    with tel.task("T001"):
        with attempt(tel) as handle:
            assert not handle.finish(row())["export_enqueued"]
    assert tel.client is None and len(tel.receipt()["attempts"]) == 1


def test_secret_redaction_retains_normal_research_text(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "private-key-123456789")
    tel, _ = make()
    value = tel.sanitize({"api_key": "anything", "headers": {"Authorization": "Bearer x"},
                          "text": "body private-key-123456789 remains", "tokens": 12})
    assert value["api_key"] == "[REDACTED]" and value["headers"] == "[REDACTED]"
    assert value["text"] == "body [REDACTED] remains" and value["tokens"] == 12


def test_replay_only_exports_saved_record_with_original_time_metadata():
    tel, client = make()
    start = {"key": "T001_writer__a01", "role": "writer", "payload": {"brief": "saved"},
             "candidate": {"model": "frozen", "provider": "openai"}, "request": {},
             "created_at": "2026-09-07T08:00:00+00:00"}
    receipt = tel.replay_attempt(start, row(), task_id="T001")
    assert receipt["ledger_replay"]
    assert receipt["original_created_at"] == start["created_at"]
    assert len(client.calls) == 2


def test_installed_sdk_supports_exact_manual_interface():
    import inspect
    from langfuse import Langfuse
    from langfuse._client.span import LangfuseGeneration
    sig = inspect.signature(Langfuse.start_as_current_observation).parameters
    assert {"trace_context", "as_type", "input", "model", "model_parameters", "metadata"} <= set(sig)
    update = inspect.signature(LangfuseGeneration.update).parameters
    assert {"output", "usage_details", "cost_details", "status_message"} <= set(update)


def test_lazy_client_construction_mask_keyword_and_environment_loading(monkeypatch):
    import langfuse
    captured = {}
    def fake_constructor(**kwargs):
        captured.update(kwargs)
        return FakeClient()
    monkeypatch.setattr(langfuse, "Langfuse", fake_constructor)
    tel = Telemetry("constructor-test")
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "test-public-value-123456")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "test-secret-value-123456")
    monkeypatch.setenv("LANGFUSE_HOST", "https://example.invalid")
    monkeypatch.setenv("OTEL_SDK_DISABLED", "false")
    monkeypatch.setenv("LANGFUSE_TRACING_ENABLED", "true")
    assert tel.healthcheck()["ready_for_paid_calls"]
    assert captured["mask"](data="test-secret-value-123456") == "[REDACTED]"
    assert captured["tracing_enabled"] and captured["sample_rate"] == 1.0
    assert captured["host"] == "https://example.invalid"
