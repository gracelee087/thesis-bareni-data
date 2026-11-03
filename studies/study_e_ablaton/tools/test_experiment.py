import copy
import unittest
from experiment import optimizer_payload, evaluation_payload, run_pair

def fixture():
    return dict(item_id='SEA-I001',initial=dict(title='Title',body='x'*200),
        context=dict(task=dict(brief='Brief',required=[],preserve=[],prohibited=[],
                              research=dict(company_evidence=[],task_evidence=[])),
                     planner={'plan':'Original'},researcher={'claims':[]},selected_lessons=[]))

class ExperimentTests(unittest.TestCase):
    def test_only_repairs_differ(self):
        item=fixture();g={'defects':[{'reason':'Unsupported claim'}]}
        on=optimizer_payload(item,item['initial'],g,[{'instruction':'Repair'}],'POST-1')
        off=optimizer_payload(item,item['initial'],g,[],'POST-1')
        on['critic_repairs']=[]
        self.assertEqual(on,off)
        self.assertNotIn('adequate',str(off))

    def test_blinding_whitelist(self):
        item=fixture(); item['old_scores']=[5]*4;item['context']['planner']['arm']='critic_on'
        output=evaluation_payload(item,item['initial'],'opaque')
        self.assertNotIn('critic_on',str(output));self.assertNotIn('old_scores',str(output))
        self.assertNotIn('planner',output)

    def test_pair_paths_and_state_isolation(self):
        item=fixture();original=copy.deepcopy(item);calls=[]
        def call(role,payload,metadata):
            calls.append((role,copy.deepcopy(payload),metadata))
            if role=='gate':return {'defects':[]}
            if role=='critic':return {'repairs':[{'instruction':'Repair'}]}
            return dict(item_id=payload['item_id'],title='Updated',body='y'*200)
        out=run_pair(item,dict(pair_id='P1',content_id='opaque',arm_order=['critic_off','critic_on']),call)
        self.assertEqual(item,original)
        self.assertEqual([x[0] for x in calls],['gate','optimizer','gate','critic','optimizer','gate'])
        self.assertEqual(out['critic_on']['history'][0]['cycle'],1)
        self.assertEqual(calls[1][1]['draft'],calls[4][1]['draft'])
        self.assertNotIn('arm',calls[1][1])

    def test_maximum_two_cycles(self):
        def call(role,payload,metadata):
            if role=='gate':return {'defects':[{'reason':'persists'}]}
            if role=='critic':return {'repairs':[]}
            return dict(item_id=payload['item_id'],title='T',body='y'*200)
        out=run_pair(fixture(),dict(pair_id='P',content_id='opaque',arm_order=['critic_on','critic_off']),call)
        self.assertTrue(all(len(x['history'])==2 for x in out.values()))

    def test_invalid_output_stops_not_substitutes(self):
        def call(role,payload,metadata):
            if role=='gate':return {'defects':[]}
            return dict(item_id='wrong',title='T',body='x'*200)
        with self.assertRaisesRegex(ValueError,'output_id_mismatch'):
            run_pair(fixture(),dict(pair_id='P',content_id='opaque',arm_order=['critic_off','critic_on']),call)

if __name__=='__main__': unittest.main()
