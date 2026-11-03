"""Freeze the user's confirmed revision, without calling a model."""
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone

S=Path(__file__).resolve().parents[2]
W=S/'private/planning_research_v2'
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def utc(): return datetime.now(timezone.utc).isoformat()
def save(p,v):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8',newline='\n') as f:
        json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False); f.write('\n')
def verify(p):
    v=read(p)
    for field in ('sha256','source_sha256','artifact_sha256'):
        for relative,h in v.get(field,{}).items():
            path=(S/relative).resolve()
            assert path.is_relative_to(S.resolve()) and digest(path)==h, relative
    return v
