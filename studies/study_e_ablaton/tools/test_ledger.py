import tempfile
import unittest
from ledger import Ledger

class LedgerTests(unittest.TestCase):
    def test_resume_does_not_call_again(self):
        with tempfile.TemporaryDirectory() as folder:
            ledger=Ledger(folder,1);calls=[]
            def invoke(request):calls.append(request);return dict(status='success',cost_usd=.1,output={'ok':True})
            ledger.call('L',{'a':1},.2,invoke);ledger.call('L',{'a':1},.2,invoke)
            self.assertEqual(len(calls),1);self.assertEqual(ledger.charge(),.1)
            with self.assertRaisesRegex(RuntimeError,'changed_resume_input'):ledger.call('L',{'a':2},.2,invoke)

    def test_interrupted_call_not_replayed(self):
        with tempfile.TemporaryDirectory() as folder:
            ledger=Ledger(folder,1)
            def crash(request):raise ConnectionError('unknown')
            with self.assertRaises(ConnectionError):ledger.call('L',{},.2,crash)
            self.assertEqual(ledger.charge(),.2)
            with self.assertRaisesRegex(RuntimeError,'interrupted_unknown'):ledger.call('L',{},.2,crash)

    def test_cap_before_call(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(RuntimeError,'budget_or_call_limit'):
                Ledger(folder,.1).call('L',{},.2,lambda _:self.fail('called provider'))

    def test_failed_usage_is_counted(self):
        with tempfile.TemporaryDirectory() as folder:
            ledger=Ledger(folder,1);calls=[]
            def invoke(request):
                calls.append(1)
                return dict(status='success' if len(calls)==2 else 'validation_failure',cost_usd=.1,output={})
            ledger.call('L',{},.2,invoke)
            self.assertEqual(ledger.charge(),.2)

if __name__=='__main__':unittest.main()
