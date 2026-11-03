import tempfile
import unittest
from pathlib import Path
from resume import RetryLedger
from ledger import save_new,hash_json

class RetryTests(unittest.TestCase):
    def test_remote_protocol_failure_is_recovered_not_skipped(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);request={'identical':'evaluation_request'}
            save_new(root/'started/L__a01.json',dict(request=request,request_sha256=hash_json(request),reserved_usd=.2))
            save_new(root/'results/L__a01.json',dict(status='transport_failure',error_kind='RemoteProtocolError',http_status=None,cost_usd=None,fatal=True))
            ledger=RetryLedger(root,1);calls=[]
            def invoke(value):
                calls.append(value)
                return dict(status='success',cost_usd=.1,output={'valid':True})
            self.assertEqual(ledger.call('L',request,.2,invoke),{'valid':True})
            self.assertEqual(calls,[request])
            self.assertAlmostEqual(ledger.charge(),.3)
            self.assertTrue((root/'results/L__a02.json').exists())
            self.assertTrue((root/'results/L__a01.json').exists())
    def test_prior429_and_saved_success_never_called_again(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);request={'same':'input'}
            for i in (1,2):save_new(root/'started'/f'L__a{i:02}.json',dict(request=request,request_sha256=hash_json(request),reserved_usd=.2))
            save_new(root/'results/L__a01.json',dict(status='transport_failure',http_status=429,cost_usd=None,fatal=True))
            save_new(root/'results/L__a02.json',dict(status='success',cost_usd=.1,output={'ok':True}))
            ledger=RetryLedger(root,1)
            self.assertEqual(ledger.call('L',request,.2,lambda _:self.fail('duplicate')),{'ok':True})
            self.assertAlmostEqual(ledger.charge(),.3)
    def test_failed429_continues_preserving_reservation(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);request={}
            save_new(root/'started/L__a01.json',dict(request=request,request_sha256=hash_json(request),reserved_usd=.2))
            save_new(root/'results/L__a01.json',dict(status='transport_failure',http_status=429,cost_usd=None,fatal=True))
            ledger=RetryLedger(root,1)
            ledger.call('L',request,.2,lambda _:dict(status='success',cost_usd=.1,output={}))
            self.assertAlmostEqual(ledger.charge(),.3)
            self.assertTrue((root/'results/L__a01.json').exists())
    def test_budget_still_stops(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(RuntimeError,'budget_or_call_limit'):
                RetryLedger(folder,.1).call('L',{},.2,lambda _:self.fail('overbudget'))

if __name__=='__main__':unittest.main()
