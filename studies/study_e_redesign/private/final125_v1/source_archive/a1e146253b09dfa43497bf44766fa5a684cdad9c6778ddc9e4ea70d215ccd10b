import copy,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import runtime as r

class ConnectedTests(unittest.TestCase):
    def test_selected_models_and_unchanged_systems(self):
        t=r.templates()
        self.assertEqual(t['researcher']['candidate']['model'],'claude-opus-5')
        self.assertEqual(t['memory']['candidate']['model'],'gpt-5.4')
        self.assertEqual(t['critic']['candidate']['model'],'gpt-5.4-mini')
        for task in r.make_tasks():
            for role,p in [('planner',r.planner_input(task,[])),('researcher',task['research'])]:
                kw=r.request_for(role,p,t[role]);self.assertEqual(kw.get('system',kw.get('input',[{}])[0].get('content')),t[role]['system'])
    def test_writer_receives_exact_actual_plan_and_ledger(self):
        task=r.make_tasks()[0];pl={'steps':[{'instruction':'unique test instruction'}]};ledger={'ledger':[{'use_guidance':'unique restriction'}]}
        p=r.production_input(task,'writer',plan=pl,ledger=ledger);r.native_schema('writer',p)
        self.assertIn(r.json.dumps(pl),p['fixed_plan'][0]);self.assertIn('unique restriction',p['fixed_plan'][1])
    def test_fault_preserves_original_and_valid_lengths(self):
        original=dict(title='Paper check',body='This is a fictional paper comparison for an owner. Keep a human responsible for approval before any money moves. No software performs the check, and the exercise does not involve a real customer.')
        snapshot=copy.deepcopy(original);changed,_=r.inject(original)
        self.assertEqual(original,snapshot);self.assertIn(r.FAULT,changed['body']);self.assertTrue(150<=len(changed['body'])<=600)
    def test_unverified_lesson_blocked_and_provenance_preserved(self):
        p=dict(role='memory',item_id='E-MEM-851',lesson_register=[],history_events=[],batch_events=[dict(event_id='B01',status='unverified',observation='Unverified test observation.')],max_register_entries=4,max_proposals=2)
        out=dict(item_id=p['item_id'],proposals=[dict(proposal_id='P01',action='ADD',target_lesson_id=None,event_ids=['B01'],lesson_text='Test lesson.',reason='Test reason.')])
        with self.assertRaises(ValueError):r.project(out,p)
        p['batch_events'][0]['status']='confirmed';reg=r.project(out,p)
        self.assertEqual(reg[0]['text'],'Test lesson.');self.assertEqual(reg[0]['source_event_ids'],['B01'])
    def test_budget_and_failure_stop_without_retry(self):
        task=r.make_tasks()[0];calls=[]
        def fail(**kw):calls.append(kw);raise RuntimeError('offline simulated failure')
        fake={'anthropic':r.SimpleNamespace(messages=r.SimpleNamespace(create=fail))}
        plan=dict(templates=r.templates(),max_calls=27,cap_usd=6.5,prior_budget_charge_usd=6.5)
        with tempfile.TemporaryDirectory(prefix='connected-test-',dir=r.S/'private') as tmp:
            root=Path(tmp).resolve();self.assertTrue(root.is_relative_to((r.S/'private').resolve()))
            with patch.object(r,'W',root):
                r.save(root/'execution_plan.json',plan);runner=r.Runner(plan,fake)
                with self.assertRaises(r.StopRun):runner.call('test','researcher',task['research'])
                self.assertFalse(calls)
                runner.charge=0
                with self.assertRaises(r.StopRun):runner.call('test','researcher',task['research'])
                self.assertEqual(len(calls),1);self.assertGreater(runner.charge,0)
                with self.assertRaises(r.StopRun):runner.call('child','researcher',task['research'],['test'])
                self.assertEqual(len(calls),1)
    def test_empty_critique_has_explicit_preserve_path(self):
        t=r.make_tasks()[0];draft=dict(title='Test',body='This is a fictional paper worksheet for a manual check. Keep human approval before any refund or movement of money. The worksheet is not running software and no timer triggers a refund.')
        p=r.production_input(t,'optimizer',draft=draft,repairs={'repairs':[]});r.native_schema('optimizer',p)
        self.assertIn('no repairs',p['fixed_critique'][0])
    def test_evaluator_payload_contains_no_upstream_answers(self):
        task=r.make_tasks()[0];v=r.evaluator_input(task,dict(title='Example',body='A fictional example.'),'EVAL-BLIND-651')
        for forbidden in ('lesson_register','fixed_plan','candidate_id','Researcher claim ledger'):
            self.assertNotIn(forbidden,v['request']['contents'])

if __name__=='__main__':unittest.main()
