# Study D — summary

> This summary was added on 2026-10-16 for the thesis appendix. It is a short description of a historical development study; it is not part of the final evidence (STUDY-E-1).

## What was tried

A preregistered run of the marketing pipeline in which every draft is revised at least once (Proposal Figure 1 routing) and outcome quality is scored by a separate blinded evaluator instead of the routing gate. The goal was to test H1 (completion), H2 (production-cost CV below 0.25) and H3 (at least 30% fewer low-quality outputs after refinement).

## Method

- 125 tasks (`SD-416` to `SD-540`) in four batches of 31/31/31/32; lessons extracted after each batch were offered to the Planner in the next batch.
- Models (`config/models.json`): Planner, Researcher, Writer and lesson extractor `gemini-3.1-flash-lite`; Critic and Optimizer `gemini-3.6-flash`; routing gate `gpt-5.6-luna`; blinded evaluator `claude-opus-5`.
- Routing: every draft received one Critic -> Optimizer pass; the gate decided only whether a second pass was needed.
- Quality: the blinded evaluator scored the initial and final text of each task on four dimensions (1-5 each); a text was low quality if any dimension was below 3. Gate scores were reported only as a contrast. Evaluator cost was kept outside H2.
- Registered as AsPredicted #309181 (2026-09-01). Earlier registrations were excluded: #309062 ([data/excluded_309062/README.md](data/excluded_309062/README.md)) and #309138, stopped after 2 complete records ([data/excluded_309138/README.md](data/excluded_309138/README.md)).

## Results

| Measure | Value |
|---|---|
| Completed tasks (H1) | 125/125 |
| Production-cost CV (H2) | 0.185 (mean USD 0.02578 per task; total USD 3.2223) |
| Low-quality outputs, blinded evaluator (H3), initial -> final | 18 -> 0 (missing pairs 0) |
| Low-quality outputs, routing gate (contrast only), initial -> final | 23 -> 0 |
| Tasks needing a second revision | 4 (129 revision passes in total) |
| Total observed cost incl. blinded evaluation | USD 29.1041 |

Source: [data/analysis/final_analysis.json](data/analysis/final_analysis.json) (total observed cost from [RESULTS_309181.md](RESULTS_309181.md))

## Problems found

- All four batches ran one after another on a single day, 2026-09-01 ([RESULTS_309181.md](RESULTS_309181.md), deviation 2).
- The low-cost Writer was chosen partly because the selection required at least three low-quality initial outputs; the uniform premium arm produced 0/20 and would have left H3 unobservable (`MODEL_SELECTION_EVIDENCE.md`, section G.3).
- The human check of the judges was not blinded: the author compared the author's own scores with the AI scores while scoring instead of sealing them first (`HUMAN_JUDGE_VALIDATION_2026-09-02.md`).
- In the earlier registration #309062, task `SD-277` failed, so one blinded evaluation pair was missing and H3 was recorded as `UNQUALIFIED_MISSING_PAIRS` (`data/excluded_309062/analysis/final_analysis.json`).

## What changed next

- In Study E the human reference for the evaluator was built first: the author scored 30 texts before seeing any model results ([L07 model selection history](../study_e_redesign/appendix/L07_model_selection_history.md), section 1).
- Models were then selected role by role with separate tests (evaluator, gate, Writer and Optimizer, Planner/Researcher, Critic, lesson curator) before being assigned to the pipeline (same file, sections 2-11).
