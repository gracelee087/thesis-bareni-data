# Experiment A and B — summary

> This summary was added on 2026-10-16 for the thesis appendix. It is a short description of a historical development study; it is not part of the final evidence (STUDY-E-1).

In the thesis these runs are called Experiment A and B; this folder name (`study_e`) is historical and is unrelated to the final Study E.

## What was tried

Two literal readings of the Proposal's refinement trigger were run on the same 125 topics as Study D, with H3
measured the way Proposal Section 9 states: by the same gate scores that route the loop. The goal was to see
how each reading behaves on cost variation (H2) and on gate-measured quality (H3).

## Method

- 125 tasks per arm (`SD-416`–`SD-540`, the Study D topics), batches 31/31/31/32, empty lesson register at start.
- Arm A (`routing_mode: unconditional_first`, Figure 1 reading): Critic → Optimizer always run once; the gate after the Optimizer decides only whether a second pass runs.
- Arm B (`routing_mode: gate_before_first`, Section 9 reading): the gate scores the draft first; only a draft with any dimension below 3, a critical violation or a length outside 150–600 characters enters Critic → Optimizer.
- Models (both arms): planner, researcher, writer, lesson extractor `gemini-3.1-flash-lite`; critic, optimizer `gemini-3.6-flash`; gate judge `gpt-5.6-luna`.
- Quality: gate judge self-scoring only (`blinded_evaluator: false`); no independent evaluator.
- Not registered on AsPredicted; each arm was frozen by a GitHub commit before its first paid call (A `1668737`, B `25b84fc`). Cost cap USD 10 per arm.

## Results

| | Arm A (Figure 1) | Arm B (Section 9 conditional) |
|---|---|---|
| Completed tasks | 125/125 | 125/125 |
| Total production cost (USD) | 3.267 | 1.770 |
| Production-cost CV (criterion < 0.25) | 0.187 (pass) | 0.660 (fail) |
| Tasks with 0 / 1 / 2 revisions | 0 / 122 / 3 | 87 / 35 / 3 |
| Mean cost by 0 / 1 / 2 revisions (USD) | – / 0.0258 / 0.0403 | 0.0086 / 0.0250 / 0.0478 |
| Low-quality texts, gate-scored, initial → final | 37 → 1 (97.3% reduction) | 36 → 0 (100% reduction) |

Source: `arm_a/data/analysis/final_analysis.json` and `arm_b/data/analysis/final_analysis.json` (summarised in [RESULTS.md](RESULTS.md))

## Problems found

- In arm B, 87 of 125 texts received no revision, which split tasks into three cost levels; the production-cost CV rose to 0.660 and H2 failed.
- H3 measured by the gate is circular: the loop stops exactly when that judge passes a text, so both arms show a 97–100% reduction.

## What changed next

- The revision trigger, not the topics, drove cost variation, so the confirmatory design keeps the route in which every text gets one revision (Study D, #309181).
- H3 is read from the independent blinded evaluator (Study D: 18 → 0), not from gate self-scoring; the confirmatory verdicts remain those of #309181.

---

## Original folder catalog (unchanged)


Two self-contained experiments that implement `Proposal.pdf` as literally as its text allows and
measure H3 exactly the way the Proposal states: with the same G-Eval assessment that routes the
refinement loop. They exist to (1) replicate the registered Study D pipeline on the same 125 tasks and
(2) show how the Proposal's own measurement rule and the two readings of its refinement trigger
behave. Neither arm replaces the confirmatory Study D verdicts (#309181).

| | arm_a | arm_b |
|---|---|---|
| Reading of the Proposal | Figure 1: Critic → Optimizer always run once; the gate after the Optimizer decides only whether a second pass runs | Section 9 sentence: the gate scores the draft first; only a draft with any dimension < 3, a critical violation or a length outside 150–600 enters Critic → Optimizer |
| `routing_mode` | `unconditional_first` | `gate_before_first` |
| Task IDs | SD-416 – SD-540 (the Study D topics, by design) | SD-416 – SD-540 (the same) |
| Paid confirmation | `RUN-STUDY-E-ARM-A` | `RUN-STUDY-E-ARM-B` |
| Smoke confirmation | `RUN-STUDY-E-ARM-A-SMOKE` | `RUN-STUDY-E-ARM-B-SMOKE` |

Common to both arms (identical to Study D unless stated):

- Models: planner / researcher / writer / lesson_extractor `gemini-3.1-flash-lite`; critic / optimizer
  `gemini-3.6-flash`; gate judge `gpt-5.6-luna`. **No blinded evaluator** (`blinded_evaluator=false`,
  `judge_eval_*` never called, measurement cost is zero by construction).
- H1 ≥ .90 (Wilson CI); H2 production-cost CV < .25 (lesson-close cost shared equally within the
  batch, every failed attempt included); H3 = relative reduction ≥ .30 in outputs with any gate
  dimension < 3, draft vs final, floor of ten initial events. **Primary test: Wilcoxon signed-rank on
  the 4–20 total (two-sided, α = .05, Pratt zeros)**; exact McNemar and the paired bootstrap are
  reported as secondary.
- Batches 31/31/31/32 run consecutively in one day; lesson memory starts empty and follows the
  Study D rules (≤ 3 ADD/MERGE/SKIP per batch close, register ≤ 12, whole register to the Planner,
  Planner selects and forwards only its selection).
- Topics: **exactly the 125 Study D #309181 topics and task IDs (SD-416–540)**, drawn again from the
  same frozen owner-written bank (bank files byte-identical to Study D's), so Study D, arm A and arm B
  are compared on identical topics. No Study D output, score, lesson or cost is read. Cost cap USD 10 per arm.
- Isolation: separate folders, separate data roots, separate confirmation strings, separate
  Langfuse `study_id` tags, branch `proposal-literal-ab`. Nothing under `studies/study_d/` is read
  or written.

Order of work per arm: offline tests → preflight → one paid live smoke on the excluded SD-001–040
pilot bank (`tools/live_smoke.py`) → `tools/freeze_manifest.py` → registration → `tools/run_all_batches.ps1`
→ `data/analysis/final_analysis.json`.
