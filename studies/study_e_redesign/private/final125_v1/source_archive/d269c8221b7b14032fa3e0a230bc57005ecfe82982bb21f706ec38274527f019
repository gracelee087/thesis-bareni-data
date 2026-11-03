"""Offline checks for the Proposal-only metrics and missing-data policy."""
import importlib.util
import math
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('proposal_analysis_test', Path(__file__).with_name('analysis.py'))
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)


class AnalysisTests(unittest.TestCase):
    def rows(self, differences=(1, 2, 3, 4)):
        def ev(values):
            return {'scores': dict(zip(a.DIMENSIONS, values))}
        return [dict(task_id=f'T{i}', status='complete', initial={'body': 'The cat sat. ' * 20},
                     final={'body': 'The cat sat. ' * 20}, initial_eval=ev([2,2,2,2]),
                     final_eval=ev([3, 2 + (d > 1), 2 + (d > 2), 2 + (d > 3)]),
                     production_completed_at='2026-09-07T12:00:02+00:00')
                for i, d in enumerate(differences)]

    def analyze(self, rows, calls=None, ids=None):
        return a.analyze(rows, calls or [dict(task_id=r['task_id'], role='optimizer', cost_usd=.1,
                                             latency_ms=100, created_at='2026-09-07T12:00:00+00:00') for r in rows],
                         expected_task_ids=ids or [r['task_id'] for r in rows], condition='mixed')

    def test_flesch_word_count_diversity_and_missing(self):
        metrics = a.text_metrics('The cat sat. The cat sat!')
        self.assertEqual(metrics['word_count'], 6)
        self.assertEqual(metrics['lexical_diversity_ttr'], .5)
        self.assertAlmostEqual(metrics['flesch_reading_ease'], 119.19)
        self.assertAlmostEqual(metrics['flesch_kincaid_grade'], -2.62)
        self.assertTrue(all(x is None for x in a.text_metrics(None).values()))
        self.assertEqual(a.text_metrics('123')['word_count'], 0)
        self.assertIsNone(a.text_metrics('123')['flesch_reading_ease'])
        self.assertIsNone(a.text_metrics('123')['lexical_diversity_ttr'])

    def test_wilcoxon_hand_reference_zero_and_missing(self):
        result = self.analyze(self.rows())
        test = result['paired_total_wilcoxon']
        self.assertEqual(test['statistic'], 0)
        # Distinct ranks 1,2,3,4: mean rank-sum=5, variance=7.5, two-sided normal tail.
        self.assertAlmostEqual(test['p_value'], math.erfc((5/math.sqrt(7.5))/math.sqrt(2)))
        self.assertEqual(test['zero_method'], 'pratt')
        rows = self.rows()
        for row in rows:
            row['final_eval'] = row['initial_eval']
        self.assertEqual(self.analyze(rows)['paired_total_wilcoxon']['p_value'], 1)
        del rows[0]['final_eval']
        result = self.analyze(rows)
        self.assertIsNone(result['paired_total_wilcoxon']['p_value'])
        self.assertIsNone(result['h3']['relative_reduction'])
        self.assertEqual(result['quality_scores']['persona_fit']['final']['n_missing'], 1)

    def test_latencies_include_failed_attempts_and_missing_is_not_zero(self):
        rows = self.rows()
        calls = [dict(task_id=r['task_id'], role='optimizer', cost_usd=.1, latency_ms=100,
                      created_at='2026-09-07T12:00:00+00:00') for r in rows]
        calls += [dict(task_id='T0', role='gate', status='failed', cost_usd=.01, latency_ms=300,
                       created_at='2026-09-07T12:00:01+00:00')]
        result = self.analyze(rows, calls)
        self.assertEqual(result['items'][0]['latency']['production_call_sum_ms'], 400)
        self.assertEqual(result['items'][0]['latency']['production_wall_clock_ms'], 2000)
        self.assertEqual(result['latency']['by_role_attempt']['gate']['n_observed'], 1)
        calls.append(dict(task_id='T0', role='gate', status='interrupted_unknown', cost_usd=None,
                          unknown_cost_reservation_usd=.5))
        result = self.analyze(rows, calls)
        self.assertIsNone(result['h2']['cv'])
        self.assertAlmostEqual(result['h2']['known_usage_cost_usd'], .41)
        self.assertIsNone(result['items'][0]['latency']['production_call_sum_ms'])
        self.assertEqual(result['items'][0]['latency']['known_attempt_latency_sum_ms'], 400)
        self.assertEqual(result['latency']['by_role_attempt']['gate']['n_missing'], 1)
        self.assertIsNone(result['items'][0]['latency']['production_wall_clock_ms'])

    def test_failed_tasks_stay_in_125_style_denominator_and_keep_actual_scores(self):
        rows = self.rows()
        rows[0]['status'] = 'failed'
        result = self.analyze(rows)
        self.assertEqual(result['h1']['complete'], 3)
        self.assertEqual(result['h1']['denominator'], 4)
        self.assertEqual(result['h3']['valid_pairs_descriptive']['n_valid_pairs'], 4)
        self.assertEqual(result['quality_scores']['total_score']['initial']['n_observed'], 4)
        self.assertIsNone(result['h2']['cv'])
        for forbidden in ('gate_by_independent_evaluation', 'gate_pass_refinement_supplement', 'strata'):
            self.assertNotIn(forbidden, result)
        for forbidden in ('paired_bootstrap95', 'missing_outcome_sensitivity'):
            self.assertNotIn(forbidden, result['h3'])
        with self.assertRaisesRegex(ValueError, 'Duplicate or unplanned'):
            self.analyze(rows + rows[:1], ids=[r['task_id'] for r in rows])


if __name__ == '__main__':
    unittest.main()

