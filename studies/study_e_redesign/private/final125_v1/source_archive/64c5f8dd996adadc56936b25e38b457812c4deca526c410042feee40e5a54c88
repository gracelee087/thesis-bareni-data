"""Offline reporting invariants: provenance, missingness, reuse, and cost isolation."""
import csv
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("final_report_under_test", HERE / "report.py")
report = importlib.util.module_from_spec(spec)
spec.loader.exec_module(report)


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.workspace = Path(self.temp.name) / "raw"
        self.output = Path(self.temp.name) / "reports"
        ids = [f"SE-FINAL-N{i:03}" for i in range(1, 126)]
        kinds = ("fabricated_evidence", "wrong_audience", "no_actionable_step", "incoherent")
        assignment = {task_id: dict(defect_type=kinds[i // 13], variant=i % 13) for i, task_id in enumerate(ids[:52])}
        self.plan = dict(tasks=[dict(task_id=t, batch_id=1 + (i >= 31) + (i >= 62) + (i >= 93), condition="natural") for i, t in enumerate(ids)],
                         mixed_order=ids, mixed_assignment=assignment, seed=20260907)
        self.put("execution_plan.json", self.plan)

    def put(self, path, value):
        path = self.workspace / path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding="utf-8")

    def attempt(self, task_id, stage, output, cost=.1, pending=False, batch=1):
        role = "memory" if task_id is None else "evaluator" if stage.startswith("eval_") else stage.rstrip("012")
        logical = f"batch{batch}_curator" if task_id is None else f"{task_id}_{stage}"
        key = logical + "__a001"
        metadata = dict(task_id=task_id, batch_id=batch, cohort="natural")
        self.put("started/" + key + ".json", dict(key=key, role=role, metadata=metadata, reserved_usd=cost, freeze_sha256="frozen"))
        if not pending:
            self.put("results/" + key + ".json", dict(key=key, role=role, metadata=metadata, cost_usd=cost,
                                                      budget_charge_usd=cost, status="success", output=output, freeze_sha256="frozen"))
        return key

    def production(self, index, measured):
        task_id = f"SE-FINAL-N{index:03}"
        text = dict(title="Title", body="x" * 200)
        gate = dict(defects=[])
        keys = {}
        for stage in ("planner", "researcher", "writer", "gate0", "critic1", "optimizer1", "gate1"):
            output = text if stage in ("writer", "optimizer1") else gate if stage.startswith("gate") else dict(repairs=[])
            keys[stage] = self.attempt(task_id, stage, output)
        row = dict(task_id=task_id, batch_id=1, condition="natural", status="complete", execution_status="complete",
                   initial=text, final=text, initial_gate=gate, final_gate=gate,
                   planner_key=keys["planner"], researcher_key=keys["researcher"], writer_key=keys["writer"],
                   final_key=keys["optimizer1"], final_gate_key=keys["gate1"], selected_lessons=[],
                   cycles=[dict(critique=dict(repairs=[]))], measurement_status="pending")
        if measured:
            evaluation = dict(scores=dict(persona_fit=4, clarity=4, actionability=4, factual_grounding=4), total_score=16,
                              critical_violation=False, **{"pass": True})
            key = self.attempt(task_id, "eval_initial", evaluation)
            row.update(initial_eval=evaluation, final_eval=evaluation, evaluation_reused=True,
                       evaluation_keys=[key, key], measurement_status="complete")
            self.put("tasks/" + task_id + ".json", row)
            # A stale checkpoint must not override the completed task record.
            self.put("production/" + task_id + ".json", dict(row, final=dict(title="stale", body="z" * 200)))
        else:
            self.put("production/" + task_id + ".json", row)
        return task_id

    def test_unstarted_keeps_both_denominators(self):
        receipt = report.build_reports(self.workspace, self.output)
        self.assertEqual(receipt["rows_written"], {"natural": 125, "mixed": 125})
        for name in ("natural", "mixed"):
            analysis = json.loads((self.output / f"{name}_analysis.json").read_text())
            self.assertEqual(analysis["report_status"], "not_started")
            self.assertEqual(analysis["h1"]["denominator"], 125)
            self.assertIsNone(analysis["h3"]["relative_reduction"])
            self.assertIsNone(analysis["paired_total_wilcoxon"]["p_value"])
            self.assertNotIn("gate_by_independent_evaluation", analysis)
            self.assertNotIn("gate_pass_refinement_supplement", analysis)
            self.assertEqual(analysis["text_metrics"]["word_count"]["initial"]["n_missing"], 125)
        with (self.output / "text_metrics_500.csv").open(encoding="utf-8-sig", newline="") as handle:
            texts = list(csv.DictReader(handle))
        self.assertEqual(len(texts), 500)
        self.assertTrue(all(row["word_count"] == "" for row in texts))
        self.assertIn("latency_descriptive.csv", receipt["output_sha256"])

    def test_production_fallback_reuse_pending_cost_and_batch_scope(self):
        first = self.production(1, True)
        second = self.production(2, False)
        pending = self.attempt(second, "eval_initial", None, cost=.7, pending=True)
        self.attempt(None, "memory", {}, cost=.31)
        before = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in self.workspace.rglob("*.json")}
        receipt = report.build_reports(self.workspace, self.output)
        self.assertEqual(receipt["unresolved_started_calls"], [pending])
        analysis = json.loads((self.output / "natural_analysis.json").read_text())
        self.assertEqual(analysis["h1"]["complete"], 2)
        self.assertIsNone(analysis["h3"]["relative_reduction"])
        self.assertEqual(analysis["h3"]["valid_pairs_descriptive"]["n_valid_pairs"], 1)
        self.assertEqual(analysis["role_cost_ledger"]["evaluator"]["unknown_reservation_usd"], .7)
        with (self.output / "natural_activity_125.csv").open(encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 125)
        self.assertEqual(rows[0]["record_source"], "tasks")
        self.assertEqual(rows[1]["record_source"], "production")
        self.assertEqual(rows[0]["initial_eval"], "O")
        self.assertEqual(rows[0]["final_eval"], "X")
        self.assertEqual(rows[0]["final_eval_source"], "reused_initial_evaluation")
        self.assertEqual(rows[1]["initial_eval_successes"], "0")
        self.assertEqual(rows[0]["natural_batch_Curator_attempts"], "1")
        self.assertFalse((self.workspace / "results" / (pending + ".json")).exists())
        self.assertTrue(receipt["source_snapshot_unchanged"])
        self.assertEqual(before, {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in self.workspace.rglob("*.json")})
        # Cohort metadata cannot reassign the same keyed call to another study arm.
        path = self.workspace / "results" / (first + "_planner__a001.json")
        value = json.loads(path.read_text()); value["metadata"]["cohort"] = "mixed"
        self.put(path.relative_to(self.workspace), value)
        with self.assertRaisesRegex(ValueError, "metadata disagreement"):
            report.build_reports(self.workspace, self.output)

    def test_orphan_result_and_raw_output_directory_rejected(self):
        key = "SE-FINAL-N001_writer__a001"
        self.put("results/" + key + ".json", dict(key=key, role="writer", status="success", cost_usd=.1))
        with self.assertRaisesRegex(ValueError, "without matching immutable start"):
            report.build_reports(self.workspace, self.output)
        with self.assertRaisesRegex(ValueError, "raw-record directory"):
            report.build_reports(self.workspace, self.workspace / "results")


if __name__ == "__main__":
    unittest.main()
