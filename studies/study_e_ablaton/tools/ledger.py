"""Sequential durable call ledger. Network implementation is injected and tested."""
import hashlib
import json
import math
import threading
from pathlib import Path
from experiment import STUDY_ID

def hash_json(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,allow_nan=False).encode()).hexdigest()

def save_new(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8') as out:json.dump(value,out,ensure_ascii=False,indent=2)

class Ledger:
    def __init__(self,root,cap_usd,max_attempts=15000):
        if cap_usd is None or cap_usd<=0:raise ValueError('explicit_positive_budget_required')
        self.root=Path(root);self.cap=cap_usd;self.max_attempts=max_attempts
        self.lock=threading.RLock()
        self._charge=self.charge()
        self._count=len(list((self.root/'started').glob('*.json')))

    def charge(self):
        value=0
        for path in (self.root/'started').glob('*.json'):
            start=json.loads(path.read_text(encoding='utf-8'))
            result=self.root/'results'/path.name
            row=json.loads(result.read_text(encoding='utf-8')) if result.exists() else {}
            value+=row.get('cost_usd') if row.get('cost_usd') is not None else start['reserved_usd']
        return value

    def call(self,logical,request,reserved_usd,invoke,max_tries=3,after_record=None):
        if not math.isfinite(reserved_usd) or reserved_usd<=0:raise ValueError('invalid_reservation')
        fingerprint=hash_json(request)
        for attempt in range(1,max_tries+1):
            name=f'{logical}__a{attempt:02}.json'
            start_path=self.root/'started'/name;result_path=self.root/'results'/name
            if start_path.exists():
                start=json.loads(start_path.read_text(encoding='utf-8'))
                if start['request_sha256']!=fingerprint:raise RuntimeError('changed_resume_input')
                if not result_path.exists():raise RuntimeError('interrupted_unknown_manual_reconciliation_required')
                result=json.loads(result_path.read_text(encoding='utf-8'))
                if result['status']=='success':return result['output']
                if result.get('fatal'):raise RuntimeError('fatal_previous_attempt')
                continue
            with self.lock:
                if self._count>=self.max_attempts or self._charge+reserved_usd>self.cap:
                    raise RuntimeError('budget_or_call_limit')
                save_new(start_path,dict(study_id=STUDY_ID,request=request,request_sha256=fingerprint,reserved_usd=reserved_usd))
                self._count+=1;self._charge+=reserved_usd
            # Unexpected exceptions leave a durable unresolved start. Never silently repeat it.
            result=invoke(request)
            if result.get('cost_usd') is not None and (not math.isfinite(result['cost_usd']) or result['cost_usd']<0):raise ValueError('invalid_cost')
            save_new(result_path,dict(result,study_id=STUDY_ID))
            with self.lock:
                if result.get('cost_usd') is not None:self._charge+=result['cost_usd']-reserved_usd
            if after_record is not None:after_record(name,result)
            if result.get('fatal'):raise RuntimeError('fatal_attempt')
            if result['status']=='success':return result['output']
        raise RuntimeError('retry_limit')
