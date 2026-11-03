import unittest
from analysis import analyze
from experiment import STUDY_ID,DIMENSIONS

def rows(delta=0):
    return [dict(study_id=STUDY_ID,item_id=f'I{i}',repeat=r,arm=a,status='complete',
                 scores=dict(zip(DIMENSIONS,[3+(delta if a=='critic_on' else 0),3,3,3])))
            for i in range(12) for r in (1,2,3) for a in ('critic_on','critic_off')]

class AnalysisTests(unittest.TestCase):
    def test_null(self):
        out=analyze(rows(),[f'I{i}' for i in range(12)],draws=1000)
        self.assertEqual(out['paired_randomization']['p_two_sided'],1)
        self.assertEqual(out['mean_difference_on_minus_off'],0)

    def test_direction_and_repeat_unit(self):
        out=analyze(rows(1),[f'I{i}' for i in range(12)],draws=10000)
        self.assertEqual(out['n_source_tasks'],12)
        self.assertEqual(out['planned_outputs'],72)
        self.assertEqual(out['mean_difference_on_minus_off'],1)
        self.assertLess(out['paired_randomization']['p_two_sided'],.01)

    def test_incomplete_no_primary_test(self):
        out=analyze(rows()[:-1],[f'I{i}' for i in range(12)])
        self.assertEqual(out['status'],'incomplete_no_primary_test')
        self.assertNotIn('paired_randomization',out)

    def test_wrong_study_rejected(self):
        data=rows(); data[0]['study_id']='STUDY-E-1'
        with self.assertRaisesRegex(ValueError,'wrong_study'): analyze(data,[f'I{i}' for i in range(12)])

    def test_duplicate_rejected(self):
        data=rows()
        with self.assertRaisesRegex(ValueError,'duplicate'):analyze(data+[data[0]],[f'I{i}' for i in range(12)])

if __name__=='__main__':unittest.main()
