"""User-authorized operational retry extension; frozen science stays unchanged."""
import hashlib
import json
import math
from pathlib import Path
import sys
import threading
import time
from datetime import datetime,timezone
BASE=Path(__file__).resolve().parent;W=BASE/'private'
sys.path.insert(0,str(BASE/'tools'))
from ledger import Ledger,hash_json,save_new
from experiment import STUDY_ID

def retryable(row):
    return (row.get('status')=='validation_failure' or
        (row.get('status')=='transport_failure' and
         (row.get('http_status') in (408,429,500,502,503,504) or
          row.get('error_kind') in ('APITimeoutError','APIConnectionError','TimeoutError','ConnectError','ReadTimeout'))))

class RetryLedger(Ledger):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.pacing=threading.Lock();self.next_call=0

    def pace(self):
        while True:
            with self.pacing:
                delay=self.next_call-time.monotonic()
                if delay<=0:
                    self.next_call=time.monotonic()+1
                    return
            time.sleep(min(delay,30))

    def call(self,logical,request,reserved_usd,invoke,max_tries=3,after_record=None):
        if not math.isfinite(reserved_usd) or reserved_usd<=0:raise ValueError('invalid_reservation')
        fingerprint=hash_json(request)
        # User explicitly extended technical retries. Budget/call cap still applies.
        for attempt in range(1,self.max_attempts+1):
            name=f'{logical}__a{attempt:02}.json'
            start_path=self.root/'started'/name;result_path=self.root/'results'/name
            if start_path.exists():
                start=json.loads(start_path.read_text(encoding='utf-8'))
                if start['request_sha256']!=fingerprint:raise RuntimeError('changed_resume_input')
                if not result_path.exists():raise RuntimeError('interrupted_unknown_manual_reconciliation_required')
                row=json.loads(result_path.read_text(encoding='utf-8'))
                if row['status']=='success':return row['output']
                if not retryable(row):raise RuntimeError('nontransient_previous_failure')
                continue
            self.pace()
            with self.lock:
                if self._count>=self.max_attempts or self._charge+reserved_usd>self.cap:
                    raise RuntimeError('budget_or_call_limit')
                save_new(start_path,dict(study_id=STUDY_ID,request=request,request_sha256=fingerprint,
                    reserved_usd=reserved_usd,operational_amendment='retry_extension_user_authorized.json',
                    created_at=datetime.now(timezone.utc).isoformat()))
                self._count+=1;self._charge+=reserved_usd
            row=invoke(request)
            cost=row.get('cost_usd')
            if cost is not None and (not math.isfinite(cost) or cost<0):raise ValueError('invalid_cost')
            save_new(result_path,dict(row,study_id=STUDY_ID,operational_amendment='retry_extension_user_authorized.json'))
            with self.lock:
                if cost is not None:self._charge+=cost-reserved_usd
            if after_record is not None:after_record(name,row)
            if row['status']=='success':return row['output']
            if not retryable(row):raise RuntimeError('nontransient_failure')
            delay=min(60,15*2**min(attempt,2))
            with self.pacing:self.next_call=max(self.next_call,time.monotonic()+delay)
            print('RETRY_SCHEDULED '+logical+' attempt='+str(attempt+1)+' wait_seconds='+str(delay),flush=True)
        raise RuntimeError('budget_or_call_limit')

def main():
    import live
    import run
    frozen=run.verify_freeze()
    manifest=W/'retry_extension_user_authorized.json'
    details=dict(study_id=STUDY_ID,original_freeze_sha256=frozen,
        authorization='User explicitly requested repeated retries until success; USD60 cap retained.',
        changes=['Transient transport and validation retries extended within budget and15000 total attempt cap',
                 'Global1second minimum dispatch interval;30to60second cooldown after transient failure'],
        scientific_settings_changed=False,prior_failures_preserved=True,unknown_cost_reservations_retained=True,
        code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    if manifest.exists():
        if json.loads(manifest.read_text(encoding='utf-8'))!=details:raise RuntimeError('amendment_changed')
    else:save_new(manifest,details)
    live.Ledger=RetryLedger
    run.execute()

if __name__=='__main__':main()
