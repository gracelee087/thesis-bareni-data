"""Preflight, immutable freeze, isolated generation/evaluation, and final analysis."""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
from experiment import STUDY_ID,run_pair,evaluation_payload
from ledger import save_new
from analysis import analyze

BASE=Path(__file__).resolve().parents[1];ROOT=BASE.parents[1];W=BASE/'private'
def read(path):return json.loads(path.read_text(encoding='utf-8'))
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def now():return datetime.now(timezone.utc).isoformat()
def update(path,value):
    temp=path.with_suffix('.tmp');temp.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8');os.replace(temp,path)

def science_files():
    files=list((BASE/'tools').glob('*.py'))+[BASE/'PROTOCOL.md']
    files += [W/n for n in ['inputs.json','schedule.json','source_manifest.json','role_configuration.json','pricing.json']]
    # Read-only dependencies contain contract code and prompt resources.
    src=ROOT/'studies/study_e_redesign'
    files += [p for p in src.rglob('*') if p.is_file() and 'private' not in p.parts and p.suffix in ('.py','.md','.json','.txt')]
    files += [ROOT/p for p in read(W/'source_manifest.json')['files']]
    return sorted(set(files))

def verify_sources():
    for name,expected in read(W/'source_manifest.json')['files'].items():
        if digest(ROOT/name)!=expected:raise RuntimeError('original_source_changed: '+name)

def verify_freeze():
    frozen=read(W/'FREEZE.json')
    for name,expected in frozen['files'].items():
        if digest(ROOT/name)!=expected:raise RuntimeError('frozen_file_changed: '+name)
    for name,version in frozen['sdk_versions'].items():
        if importlib.metadata.version(name)!=version:raise RuntimeError('sdk_version_changed')
    verify_sources();return digest(W/'FREEZE.json')

def freeze():
    if (W/'FREEZE.json').exists():print('Verified existing freeze '+verify_freeze());return
    verify_sources()
    result=subprocess.run([sys.executable,'-m','unittest','discover','-s',str(BASE/'tools'),'-p','test_*.py'],capture_output=True,text=True)
    print(result.stdout+result.stderr)
    if result.returncode:raise RuntimeError('offline_tests_failed')
    save_new(W/'offline_test_receipt.json',dict(at=now(),returncode=0,output=result.stdout+result.stderr))
    save_new(W/'FREEZE.json',dict(study_id=STUDY_ID,at=now(),external_preregistered=False,
        cap_usd=60,repeats=3,workers=4,
        sdk_versions={n:importlib.metadata.version(n) for n in ['openai','google-genai','langfuse','pydantic','numpy','scipy']},
        files={str(p.relative_to(ROOT)):digest(p) for p in science_files()}))
    print('FROZEN '+verify_freeze(),flush=True)

def execute():
    freeze_hash=verify_freeze()
    # OS-held lock releases even after a crash, with no stale lock bypass.
    import msvcrt
    lock=(W/'execution.lock').open('a+b');lock.seek(0)
    if not lock.read(1):lock.write(b'0');lock.flush()
    lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
    from live import Live
    live=Live(freeze_hash)
    inputs=read(W/'inputs.json')['items'];items={x['item_id']:x for x in inputs}
    schedule=read(W/'schedule.json');pairs={x['pair_id']:x for x in schedule['pairs']}
    def generate(pair):
        path=W/'pairs'/(pair['pair_id']+'.json')
        if path.exists():return
        def call(role,payload,meta):
            return live.call(role,payload,meta,pair['content_id']+'-'+str(meta['cycle']))
        result=run_pair(items[pair['item_id']],pair,call)
        save_new(path,dict(study_id=STUDY_ID,pair=pair,arms=result,freeze_sha256=freeze_hash))
        print('PAIR_COMPLETE '+pair['pair_id'],flush=True)
    def evaluate(ev):
        path=W/'evaluations'/(ev['blind_id']+'.json')
        if path.exists():return
        pair=pairs[ev['pair_id']];produced=read(W/'pairs'/(ev['pair_id']+'.json'))
        payload=evaluation_payload(items[pair['item_id']],produced['arms'][ev['arm']]['final'],ev['blind_id'])
        meta=dict(study_id=STUDY_ID,pair_id=pair['pair_id'],arm=ev['arm'],cycle='eval')
        rating=live.call('evaluator',payload,meta,ev['blind_id'])
        save_new(path,dict(study_id=STUDY_ID,item_id=pair['item_id'],repeat=pair['repeat'],
            arm=ev['arm'],blind_id=ev['blind_id'],status='complete',scores=rating['scores'],rating=rating))
        print('EVAL_COMPLETE '+ev['blind_id'],flush=True)
    def phase(jobs,worker):
        # Fixed windows preserve schedule dispatch ordering; no outcome-based scheduling.
        with ThreadPoolExecutor(max_workers=4) as pool:
            for i in range(0,len(jobs),4):
                futures=[pool.submit(worker,j) for j in jobs[i:i+4]]
                errors=[]
                for future in futures:
                    try:future.result()
                    except Exception as exc:errors.append(exc)
                update(W/'STATUS.json',dict(study_id=STUDY_ID,at=now(),status='running',
                    pairs_complete=len(list((W/'pairs').glob('*.json'))),
                    evaluations_complete=len(list((W/'evaluations').glob('*.json'))),
                    budget_charge_usd=live.ledger._charge))
                if errors:raise errors[0]
    try:
        phase(schedule['pairs'],generate)
        phase(schedule['evaluation_order'],evaluate)
        verify_freeze()
        rows=[read(p) for p in sorted((W/'evaluations').glob('*.json'))]
        report=analyze(rows,list(items))
        save_new(W/'analysis.json',report)
        update(W/'STATUS.json',dict(study_id=STUDY_ID,at=now(),status=report['status'],
            pairs_complete=375,evaluations_complete=len(rows),budget_charge_usd=live.ledger.charge()))
        print('COMPLETE',flush=True)
    except Exception as exc:
        update(W/'STATUS.json',dict(study_id=STUDY_ID,at=now(),status='stopped',error_kind=type(exc).__name__,
            reason=str(exc)[:150],pairs_complete=len(list((W/'pairs').glob('*.json'))),
            evaluations_complete=len(list((W/'evaluations').glob('*.json'))),budget_charge_usd=live.ledger.charge()))
        print('STOPPED '+type(exc).__name__+' '+str(exc)[:150],flush=True)
        raise
    finally:
        update(W/'telemetry_receipt.json',live.telemetry.flush())
        lock.close()

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['preflight','freeze','verify','execute']);args=parser.parse_args()
    if args.command=='preflight':
        from live import Live
        live=Live('preflight-no-paid-calls')
        for model in ['gpt-5.4','gpt-5.4-mini']:live.openai.models.retrieve(model)
        live.google.models.get(model='gemini-3.8-flash')
        update(W/'connection_preflight.json',dict(at=now(),langfuse_authenticated=True,models_available=True,paid_calls=0))
        print('PREFLIGHT_OK paid_calls=0');live.telemetry.flush()
    elif args.command=='freeze':freeze()
    elif args.command=='verify':print(verify_freeze())
    else:execute()
