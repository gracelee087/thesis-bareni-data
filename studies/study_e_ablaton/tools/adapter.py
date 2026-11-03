"""Compile isolated ablation requests using read-only, versioned source contracts."""
import copy
import importlib.util
import json
import sys
from pydantic import Field
from pathlib import Path
from experiment import OPTIMIZER_INSTRUCTION, validate_post

ROOT=Path(__file__).resolve().parents[3]
SOURCE=ROOT/'studies/study_e_redesign'

def load_contracts():
    name='study_e_ablaton_long_contracts'
    if name not in sys.modules:
        spec=importlib.util.spec_from_file_location(name,SOURCE/'tools/long125_v2/run.py')
        module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module)
    return sys.modules[name].rt

class Adapter:
    def __init__(self):
        self.rt=load_contracts()
        # Adapt only identifier namespaces, in this isolated process. All substantive
        # validators and rubric constraints are inherited unchanged.
        rt=self.rt
        class AblatonGateInput(rt.api.GateInput):
            item_id: str=Field(min_length=1,max_length=100)
        class AblatonGateOutput(rt.gate.GateOutput):
            item_id: str=Field(min_length=1,max_length=100)
        class AblatonRating(rt.EvaluatorRating):
            item_id: str=Field(pattern=r'^EVAL-[A-Za-z0-9-]+$')
        rt.api.GateInput=rt.gate.GateInput=AblatonGateInput
        rt.gate.GateOutput=AblatonGateOutput
        rt.EvaluatorRating=AblatonRating
        self.plan=json.loads((SOURCE/'private/final125_v1/execution_plan.json').read_text(encoding='utf-8'))

    def compile(self,role,payload,content_id):
        rt=self.rt
        if role=='evaluator':
            # payload is already a strict whitelist from evaluation_payload().
            task=dict(brief=payload['brief'],required=payload['required_content'],
                      prohibited=payload['prohibited_claims'],preserve=payload['preservation_constraints'],
                      research=dict(company_evidence=payload['company_evidence'],task_evidence=payload['task_evidence']))
            result=rt.evaluator_input(task,payload,payload['item_id'])
            return dict(provider='google',model='gemini-3.8-flash',request=result['request'],validation=result['item'])
        template=copy.deepcopy(self.plan['templates'][role])
        if role=='optimizer':
            request=template['request']
            request['input']=[dict(role='system',content=OPTIMIZER_INSTRUCTION),
                              dict(role='user',content=json.dumps(payload,ensure_ascii=False))]
            request['text']['format']['schema']=dict(type='object',additionalProperties=False,
                required=['item_id','title','body'],properties=dict(item_id=dict(type='string',enum=[payload['item_id']]),
                title=dict(type='string'),body=dict(type='string')))
            validation=payload
        else:
            task=payload['context']['task']
            gate_payload=rt.gate_input(task,payload['draft'],content_id,self.plan['templates']['gate']['rules'])
            validation=gate_payload if role=='gate' else rt.critic_input(task,payload['draft'],payload['gate_assessment'],gate_payload,'E-CRIT-'+content_id)
            request=rt.request_for(role,validation,template)
        request['service_tier']='default'
        return dict(provider=template['candidate']['provider'],model=template['candidate']['model'],
                    request=request,validation=validation)

    def validate(self,role,response,compiled):
        if role=='evaluator':
            row=self.rt.check_evaluator(response,compiled['validation'])
            if row['status']!='success':raise ValueError('invalid_evaluator_response')
            return row['output']
        raw=response.model_dump(mode='json')
        if raw.get('status')!='completed':raise ValueError('incomplete_response')
        if role=='gate':
            candidate=self.plan['templates']['gate']['candidate']
            row=self.rt.api.validate_response(response,'openai',candidate,compiled['validation'])
            if row.get('status')!='success':raise ValueError('invalid_gate_response')
            return row['rating']
        if role=='optimizer':
            value=json.loads(response.output_text);validate_post(value,compiled['validation']['item_id'])
            if set(value)!={'item_id','title','body'}:raise ValueError('extra_output_fields')
            return value
        value=self.rt.parse('critic',response.output_text,compiled['validation'])
        required=set(self.rt.cm.target_ids(compiled['validation']))
        covered={x for repair in value['repairs'] for x in repair['target_ids']}
        if not required<=covered:raise ValueError('unaddressed_gate_defect')
        return value
