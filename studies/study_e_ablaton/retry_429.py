"""One documented retry of an explicit HTTP429 rejection, preserving the request.

Operational amendment: explicit provider rejection may be retried once after
cooldown to distinguish throttling from exhausted quota. Prior cost reservations
remain charged. No successful response is repeated and no study setting changes.
"""
import json
from pathlib import Path
import sys
import time
from datetime import datetime,timezone
BASE=Path(__file__).resolve().parent;W=BASE/'private'
sys.path.insert(0,str(BASE/'tools'))
from live import Live
from ledger import save_new,hash_json
from run import verify_freeze
import pricing

def read(p):return json.loads(p.read_text(encoding='utf-8'))
def now():return datetime.now(timezone.utc).isoformat()

def main():
    freeze=verify_freeze()
    key='SEA-I056-R2-critic_off-1-optimizer__a01.json'
    name=key.replace('__a01','__a02')
    old=read(W/'ledger/results'/key);start=read(W/'ledger/started'/key)
    assert old['status']=='transport_failure' and old['http_status']==429
    assert not (W/'ledger/started'/name).exists(),'Do not repeat diagnostic retry'
    assert hash_json(start['request'])==start['request_sha256']
    save_new(W/'operational_amendment_429.json',dict(at=now(),freeze_sha256=freeze,
        reason='Explicit HTTP429 rejection; single identical-request retry after cooldown to identify quota versus rate limit.',
        old_attempt=key,new_attempt=name,old_reservation_retained=True,
        scientific_settings_changed=False,successful_calls_repeated=0,
        script_sha256=__import__('hashlib').sha256(Path(__file__).read_bytes()).hexdigest()))
    live=Live(freeze);wrapped=start['request'];c=wrapped['compiled'];meta=wrapped['metadata'];role=wrapped['role']
    assert live.ledger.charge()+start['reserved_usd']<=60
    save_new(W/'ledger/started'/name,dict(start,operational_amendment='operational_amendment_429.json',created_at=now()))
    row=dict(study_id='STUDY-E-ABLATON',created_at=now(),role=role,metadata=meta,
        freeze_sha256=freeze,status='transport_failure',output=None,usage=None,cost_usd=None)
    tick=time.monotonic()
    try:
        response=live.openai.responses.create(**c['request'])
        raw=response.model_dump(mode='json');row['provider_response']=raw
        usage=pricing.normalize_usage(c['provider'],raw);cost=pricing.cost_details(c['model'],usage,live.prices)
        row.update(usage=usage,cost_details=cost,cost_usd=cost['total'])
        import re
        assert re.fullmatch(live.prices['models'][c['model']]['match_pattern'],raw['model'])
        assert raw.get('service_tier') in (None,'default')
        row.update(output=live.adapter.validate(role,response,c),status='success')
    except Exception as exc:
        body=getattr(exc,'body',{}) or {}
        if isinstance(body,dict) and isinstance(body.get('error'),dict):body=body['error']
        code=getattr(exc,'code',None) or (body.get('code') if isinstance(body,dict) else None)
        row.update(error_kind=type(exc).__name__,http_status=getattr(exc,'status_code',None),
            error_code=live.telemetry.safe_label(str(code)),fatal=True)
    row.update(latency_ms=round((time.monotonic()-tick)*1000),finished_at=now())
    save_new(W/'ledger/results'/name,row)
    with live.telemetry.task(meta['pair_id'],meta):
        with live.telemetry.attempt(name,role,c['validation'],dict(model=c['model'],provider=c['provider']),c['request'],meta) as handle:
            save_new(W/'telemetry'/name,handle.finish(row))
    save_new(W/'retry429_telemetry_receipt.json',live.telemetry.flush())
    print(json.dumps({k:row.get(k) for k in ['status','error_kind','http_status','error_code','cost_usd']}),flush=True)

if __name__=='__main__':main()
