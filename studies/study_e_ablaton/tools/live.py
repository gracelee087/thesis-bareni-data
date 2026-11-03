"""Isolated paid transport. SDK retries disabled; durable ledger owns retries."""
import os
import re
import time
from datetime import datetime,timezone
from pathlib import Path
import pricing
from ledger import Ledger,save_new
from telemetry import Telemetry
from adapter import Adapter

BASE=Path(__file__).resolve().parents[1]
ROOT=BASE.parents[1]

def now():return datetime.now(timezone.utc).isoformat()

class Live:
    def __init__(self,freeze_hash):
        from dotenv import load_dotenv
        load_dotenv(ROOT/'.env',override=False)
        self.adapter=Adapter()
        self.prices=pricing.load_pricing();pricing.validate_date(self.prices)
        self.freeze_hash=freeze_hash
        self.ledger=Ledger(BASE/'private/ledger',60)
        self.telemetry=Telemetry('STUDY-E-ABLATON-20260908')
        self.telemetry.healthcheck()
        from openai import OpenAI
        from google import genai
        from google.genai import types
        self.openai=OpenAI(api_key=os.environ['OPENAI_API_KEY'],max_retries=0,timeout=180)
        self.google=genai.Client(api_key=os.environ.get('GOOGLE_API_KEY') or os.environ['GEMINI_API_KEY'],
            http_options=types.HttpOptions(timeout=180000,retry_options=types.HttpRetryOptions(attempts=1)))

    def call(self,role,payload,metadata,content_id):
        compiled=self.adapter.compile(role,payload,content_id)
        logical='-'.join(str(metadata[k]) for k in ('pair_id','arm','cycle'))+'-'+role
        wrapped=dict(compiled=compiled,metadata=metadata,role=role,freeze_sha256=self.freeze_hash)
        reserved=pricing.reserve(compiled['model'],compiled['request'],self.prices)
        def invoke(_):
            begun=now();tick=time.monotonic()
            row=dict(created_at=begun,role=role,metadata=metadata,freeze_sha256=self.freeze_hash,
                status='transport_failure',output=None,cost_usd=None,usage=None)
            try:
                response=(self.openai.responses.create(**compiled['request']) if compiled['provider']=='openai'
                    else self.google.models.generate_content(**compiled['request']))
            except Exception as exc:
                # Ambiguous billing is reserved and stops the run; never silently retry.
                row.update(error_kind=type(exc).__name__,fatal=True,
                    http_status=getattr(exc,'status_code',getattr(exc,'code',None)))
                row['latency_ms']=round((time.monotonic()-tick)*1000)
                return row
            raw=response.model_dump(mode='json')
            row.update(provider_response=raw,latency_ms=round((time.monotonic()-tick)*1000),finished_at=now())
            try:
                usage=pricing.normalize_usage(compiled['provider'],raw)
                costs=pricing.cost_details(compiled['model'],usage,self.prices)
                row.update(usage=usage,cost_details=costs,cost_usd=costs['total'])
            except Exception as exc:
                row.update(status='usage_failure',error_kind=type(exc).__name__,fatal=True)
                return row
            actual=raw.get('model',raw.get('model_version',''))
            rate=self.prices['models'][compiled['model']]
            if not re.fullmatch(rate['match_pattern'],actual):
                row.update(status='model_mismatch',fatal=True);return row
            if compiled['provider']=='openai' and raw.get('service_tier') not in (None,'default'):
                row.update(status='service_tier_mismatch',fatal=True);return row
            try:
                row.update(output=self.adapter.validate(role,response,compiled),status='success')
            except Exception as exc:
                row.update(status='validation_failure',error_kind=type(exc).__name__,
                    validation_detail=str(exc)[:500])
            return row
        def after_record(name,row):
            # Export only after durable local result. Failure here cannot repeat a model call.
            try:
                candidate=dict(provider=compiled['provider'],model=compiled['model'])
                with self.telemetry.task(metadata['pair_id'],metadata):
                    with self.telemetry.attempt(name,role,payload,candidate,compiled['request'],metadata) as handle:
                        receipt=handle.finish(row)
                save_new(BASE/'private/telemetry'/name,receipt)
            except Exception as exc:
                print('TELEMETRY_ERROR '+type(exc).__name__,flush=True)
        return self.ledger.call(logical,wrapped,reserved,invoke,after_record=after_record)
