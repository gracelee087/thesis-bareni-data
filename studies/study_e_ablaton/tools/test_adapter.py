import copy
import json
import unittest
from pathlib import Path
from adapter import Adapter
from experiment import optimizer_payload,evaluation_payload

class AdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.adapter=Adapter()
        cls.items=json.loads((Path(__file__).resolve().parents[1]/'private/inputs.json').read_text(encoding='utf-8'))['items']

    def test_all_inputs_compile_and_evaluator_blinded(self):
        for item in self.items:
            draft=item['initial']; gate={'defects':[]}
            compiled=self.adapter.compile('gate',dict(draft=draft,context=item['context']),'BLIND-1')
            self.assertEqual(compiled['model'],'gpt-5.4')
            canonical=dict(schema_version='study-e-gate-v4',item_id='BLIND-1',assessment_status='assessed',input_problem_reason=None,defects=[])
            rt=self.adapter.rt
            rt.gate.validate_output(canonical,rt.gate.GateInput.model_validate(compiled['validation']))
            critic=self.adapter.compile('critic',dict(draft=draft,context=item['context'],gate_assessment=canonical),'BLIND-1')
            self.assertEqual(critic['validation']['body_length_bounds']['max'],2000)
            on=optimizer_payload(item,draft,gate,[{'instruction':'Repair'}],'POST-1')
            off=optimizer_payload(item,draft,gate,[],'POST-1')
            a=self.adapter.compile('optimizer',on,'POST-1')['request']
            b=self.adapter.compile('optimizer',off,'POST-1')['request']
            decoded=json.loads(a['input'][1]['content']);decoded['critic_repairs']=[]
            self.assertEqual(decoded,json.loads(b['input'][1]['content']))
            a=copy.deepcopy(a);b=copy.deepcopy(b);a.pop('input');b.pop('input');self.assertEqual(a,b)
            ev=evaluation_payload(item,draft,'EVAL-opaque')
            request=self.adapter.compile('evaluator',ev,'EVAL-opaque')['request']
            self.assertNotIn('critic_on',json.dumps(request));self.assertNotIn('critic_off',json.dumps(request))
            self.assertNotIn(item['item_id'],json.dumps(request))

if __name__=='__main__':unittest.main()
