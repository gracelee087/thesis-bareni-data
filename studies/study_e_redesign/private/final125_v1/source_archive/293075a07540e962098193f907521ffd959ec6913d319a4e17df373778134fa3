"""Offline checks for the NEW final runner. Never execute a model or export traces.

Each subprocess rejects socket connections and receives no provider credentials.
Timestamped evidence is immutable; offline_test_receipt.json is a latest index.
Freeze must compare this receipt's source_sha256 with run.source_files() hashes.
"""
from __future__ import annotations

from datetime import datetime, timezone
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from preparation import ROOT, W, digest, read
from telemetry import Telemetry


NETWORK_GUARD = """
import socket
def _no_network(*args, **kwargs):
    raise RuntimeError('Offline checks prohibit network and provider calls')
socket.socket.connect = _no_network
socket.socket.connect_ex = _no_network
socket.socket.sendto = _no_network
socket.create_connection = _no_network
"""


def utc():
    return datetime.now(timezone.utc).isoformat()


def save_new(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def load_runner():
    # Imports compile contracts only; does not construct clients or execute graphs.
    spec = importlib.util.spec_from_file_location('final_offline_runner', HERE/'run.py')
    runner = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = runner
    spec.loader.exec_module(runner)
    return runner


def source_hashes(runner):
    return {path.relative_to(ROOT).as_posix(): digest(path)
            for path in runner.source_files()}


def versions():
    pins = {}
    for line in (HERE/'requirements.lock.txt').read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if line and not line.startswith('#'):
            name, sep, expected = line.partition('==')
            if not sep or not name or not expected:
                raise ValueError('Every dependency must have an exact == pin')
            pins[name] = expected
    actual = {}
    for name in pins:
        try:
            actual[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            actual[name] = None
    return pins, actual


def child_environment():
    env = {key: value for key, value in os.environ.items()
           if not re.search(r'KEY|SECRET|TOKEN|PASSWORD', key, re.I)}
    env.update(PYTHONUTF8='1', PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',
               LANGFUSE_TRACING_ENABLED='false', OTEL_SDK_DISABLED='true',
               LANGCHAIN_TRACING_V2='false', LANGSMITH_TRACING='false')
    return env


def run_check(name, bootstrap, args, folder, sanitizer):
    command = [sys.executable, '-X', 'utf8', '-c', NETWORK_GUARD + bootstrap, *args]
    started = utc()
    try:
        result = subprocess.run(command, cwd=ROOT, env=child_environment(),
                                capture_output=True, text=True, encoding='utf-8',
                                errors='replace', timeout=600)
        output = sanitizer.sanitize(result.stdout + '\n' + result.stderr)
        code = result.returncode
        error_kind = None
    except subprocess.TimeoutExpired as exc:
        def decode(value):
            return value.decode('utf-8', errors='replace') if isinstance(value, bytes) else (value or '')
        output = sanitizer.sanitize(decode(exc.stdout) + '\n' + decode(exc.stderr))
        code, error_kind = None, 'TimeoutExpired'
    logpath = folder/(name + '.log')
    with logpath.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(output)
    return dict(started_at=started, ended_at=utc(), exit_code=code,
                passed=code == 0, error_kind=error_kind,
                command_kind=name, network_policy='socket connections disabled; no provider credentials',
                log_path=logpath.relative_to(ROOT).as_posix(), log_sha256=digest(logpath),
                output_tail=output[-8000:])


def main():
    if not (W/'execution_plan.json').exists():
        raise SystemExit('Run the offline prepare command first; no final execution plan exists.')
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S') + '_' + str(time.time_ns())
    folder = W/'offline_checks'/stamp
    folder.mkdir(parents=True, exist_ok=False)
    sanitizer = Telemetry('offline-check', enabled=False)
    report = dict(schema_version='study-e-final-offline-check-v1', started_at=utc(),
                  check_id=stamp, passed=False, model_api_calls=0, cloud_uploads=0,
                  latest_receipt_is_mutable_index=True,
                  immutable_receipt_path=(folder/'receipt.json').relative_to(ROOT).as_posix())
    try:
        runner = load_runner()
        before = source_hashes(runner)
        report['source_sha256'] = before
        report['tested_runtime_sha256'] = before[(HERE/'run.py').relative_to(ROOT).as_posix()]
        report['plan_sha256'] = digest(W/'execution_plan.json')
        pins, installed = versions()
        report.update(pinned_versions=pins, installed_versions=installed,
                      versions_match_pins=pins == installed, python_version=sys.version)
        tests = sorted(HERE.glob('test_*.py'))
        if not tests:
            raise RuntimeError('No final runner tests were found')
        report['test_files'] = [path.relative_to(ROOT).as_posix() for path in tests]
        pytest_bootstrap = "\nimport sys, pytest\nraise SystemExit(pytest.main(sys.argv[1:]))\n"
        report['pytest'] = run_check('pytest', pytest_bootstrap,
            ['-q', *[str(path) for path in tests]], folder, sanitizer)
        analysis_bootstrap = "\nimport sys, runpy\npath=sys.argv[1]\nsys.argv=sys.argv[1:]\nrunpy.run_path(path, run_name='__main__')\n"
        report['analysis_self_test'] = run_check('analysis_self_test', analysis_bootstrap,
            [str(HERE/'analysis.py'), '--self-test'], folder, sanitizer)
        # Build the actual LangGraph topology without invoking any node or Runner.
        graph = runner.build_graph(SimpleNamespace(plan=read(W/'execution_plan.json')))
        graph_text = graph.get_graph().draw_mermaid()
        graphpath = folder/'task_graph.mmd'
        with graphpath.open('x', encoding='utf-8', newline='\n') as stream:
            stream.write(graph_text + '\n')
        report['graph'] = dict(path=graphpath.relative_to(ROOT).as_posix(),
                              sha256=digest(graphpath), source='actual compiled LangGraph get_graph()',
                              nodes_invoked=0, includes='natural and mixed task routes; batch curator is separate')
        after = source_hashes(runner)
        report['source_hashes_unchanged'] = before == after
        if before != after:
            report['source_sha256_after'] = after
        report['plan_hash_unchanged'] = report['plan_sha256'] == digest(W/'execution_plan.json')
        report['passed'] = all([report['pytest']['passed'], report['analysis_self_test']['passed'],
            report['versions_match_pins'], report['source_hashes_unchanged'], report['plan_hash_unchanged']])
    except Exception as exc:
        report['error_kind'] = type(exc).__name__
        # No exception body: lower-level clients may put credentials in messages.
    report['completed_at'] = utc()
    save_new(folder/'receipt.json', report)
    latest = W/'offline_test_receipt.json'
    temporary = W/('offline_test_receipt.' + stamp + '.tmp')
    save_new(temporary, report)
    os.replace(temporary, latest)  # Timestamped originals remain untouched.
    print(json.dumps({key: report.get(key) for key in
        ['passed', 'check_id', 'model_api_calls', 'cloud_uploads', 'source_hashes_unchanged',
         'versions_match_pins', 'error_kind']}, ensure_ascii=False))
    raise SystemExit(0 if report['passed'] else 1)


if __name__ == '__main__':
    main()
