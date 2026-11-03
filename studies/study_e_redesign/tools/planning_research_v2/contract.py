"""Same local contract, with the existing source-ID domain exposed natively."""
import importlib.util
from pathlib import Path
_path=Path(__file__).resolve().parents[1]/'planning_research_v1/contract.py'
_spec=importlib.util.spec_from_file_location('planning_contract_v1',_path)
_base=importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_base)
validate_input=_base.validate_input
validate_output=_base.validate_output
parse=_base.parse
observable_checks=_base.observable_checks
def schema(p):
    result=_base.schema(p)
    ids=[s['source_id'] for s in p['company_evidence']+p['task_evidence']]
    domain=dict(type='string',enum=ids)
    if p['role']=='planner':
        result['properties']['steps']['items']['properties']['evidence_ids']['items']=domain
    else:
        result['properties']['ledger']['items']['properties']['evidence']['items']['properties']['source_id']=domain
    return result
