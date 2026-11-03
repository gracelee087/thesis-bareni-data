"""Compact request-bound wire schema and lossless canonical field expansion."""
from copy import deepcopy
import json

from jsonschema import Draft202012Validator, ValidationError

from gate_contract import GateInput, GateOutput


SCHEMA_VERSION='study-e-gate-v4'
WIRE_VERSION='study-e-gate-wire-v4'


def fixed(value):
    return {'type':'string','enum':[value]}


def strict_object(properties):
    return {'type':'object','properties':properties,'required':list(properties),
            'additionalProperties':False}


def request_schema(request: GateInput) -> dict:
    sources=[request.brief.source_id,*(s.source_id for s in request.evidence)]
    location={'anyOf':[
        strict_object({
            'location_kind':fixed('quote'),
            'text_field':{'type':'string','enum':['title','body']},
            'quote':{'type':'string','minLength':1},
        }),
        strict_object({
            'location_kind':fixed('omission'),
            'missing_requirement':{'type':'string','minLength':1},
        }),
    ]}
    defect=strict_object({
        'rule_id':{'type':'string','enum':[rule.rule_id for rule in request.rules]},
        'location':location,
        'evidence_ids':{'type':'array','minItems':1,'items':{'type':'string','enum':sources}},
        'reason':{'type':'string','minLength':1},
    })
    return strict_object({
        'schema_version':fixed(WIRE_VERSION),'item_id':fixed(request.item_id),
        'assessment_status':{'type':'string','enum':['assessed','input_problem']},
        'input_problem_reason':{'anyOf':[{'type':'string','minLength':1},{'type':'null'}]},
        'defects':{'type':'array','items':defect},
    })


def provider_schema(provider: str, request: GateInput) -> dict:
    schema=request_schema(request)
    if provider=='openai': return schema
    if provider=='anthropic':
        from anthropic import transform_schema
        return transform_schema(deepcopy(schema))
    raise ValueError('unsupported provider')


def normalize_wire(raw: dict | str, request: GateInput) -> dict:
    """Validate first, then copy selected rule metadata and canonical null fields.

    This never changes a selected rule, source, quotation, omission, or reason.
    The caller must subsequently run validate_output for relational constraints.
    """
    try:
        wire=json.loads(raw) if isinstance(raw,str) else raw
        Draft202012Validator(request_schema(request)).validate(wire)
    except (json.JSONDecodeError, ValidationError) as exc:
        raise ValueError('invalid gate wire output: '+str(exc.message if isinstance(exc,ValidationError) else exc)) from exc
    rules={rule.rule_id:rule for rule in request.rules}
    canonical={
        'schema_version':SCHEMA_VERSION,
        'item_id':wire['item_id'],
        'assessment_status':wire['assessment_status'],
        'input_problem_reason':wire['input_problem_reason'],
        'defects':[],
    }
    for defect in wire['defects']:
        rule=rules[defect['rule_id']]
        location=defect['location']
        is_quote=location['location_kind']=='quote'
        canonical['defects'].append({
            'dimension':rule.dimension,
            'severity':rule.severity,
            'location_kind':location['location_kind'],
            'text_field':location['text_field'] if is_quote else None,
            'quote':location['quote'] if is_quote else None,
            'missing_requirement':None if is_quote else location['missing_requirement'],
            'rule_id':defect['rule_id'],
            'evidence_ids':list(defect['evidence_ids']),
            'reason':defect['reason'],
        })
    return canonical


def to_wire(canonical: dict) -> dict:
    """Convert valid canonical fixtures to wire form; not a response repair path."""
    output=GateOutput.model_validate(canonical).model_dump()
    wire={key:value for key,value in output.items() if key!='defects'}
    wire['schema_version']=WIRE_VERSION
    wire['defects']=[]
    for defect in output['defects']:
        location={'location_kind':defect['location_kind']}
        if defect['location_kind']=='quote':
            location.update(text_field=defect['text_field'],quote=defect['quote'])
        else:
            location['missing_requirement']=defect['missing_requirement']
        wire['defects'].append({
            'rule_id':defect['rule_id'],
            'location':location,
            'evidence_ids':list(defect['evidence_ids']),
            'reason':defect['reason'],
        })
    return wire
