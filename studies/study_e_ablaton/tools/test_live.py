import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from ledger import Ledger

class ConcurrencyTests(unittest.TestCase):
    def test_reservations_bound_concurrent_requests(self):
        import threading
        with tempfile.TemporaryDirectory() as folder:
            ledger=Ledger(folder,.5);release=threading.Event();entered=threading.Event()
            def invoke(_):
                entered.set();release.wait(2)
                return dict(status='success',cost_usd=.3,output={})
            with ThreadPoolExecutor(max_workers=2) as pool:
                first=pool.submit(ledger.call,'first',{},.3,invoke)
                self.assertTrue(entered.wait(2))
                with self.assertRaisesRegex(RuntimeError,'budget_or_call_limit'):
                    ledger.call('second',{},.3,lambda _:self.fail('over-budget call'))
                release.set();first.result()
            self.assertAlmostEqual(ledger.charge(),.3)
    def test_record_before_telemetry(self):
        from pathlib import Path
        with tempfile.TemporaryDirectory() as folder:
            ledger=Ledger(folder,1);seen=[]
            def after(name,row):
                self.assertTrue((Path(folder)/'results'/name).exists());seen.append(name)
            ledger.call('one',{},.2,lambda _:dict(status='success',cost_usd=.1,output={}),after_record=after)
            self.assertEqual(len(seen),1)

if __name__=='__main__':unittest.main()
