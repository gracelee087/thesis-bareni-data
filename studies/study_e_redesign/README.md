# Study E pilot and STUDY-E-1 — folder guide

> Added on 2026-10-16 for the thesis appendix.

This folder contains two things:

1. **Study E pilot** (historical, before the final experiment) — summarised below.
2. **STUDY-E-1** (the final experiment). Its English appendix materials are in [`appendix/`](appendix/README.md).

## Study E pilot — summary

### What was tried
Before the final experiment, the author picked one model per pipeline role, checked that the roles worked as one
connected pipeline, and then ran pilots. The question was whether the Proposal criteria (H1 completion, H2 cost
stability, H3 drop in low-quality texts) could actually be measured with this setup.

### Method
- Models per role (connection test, also used in all pilots): Planner claude-haiku-4-5-20251001; Researcher
  claude-opus-5; Writer, Critic and Optimizer gpt-5.4-mini; Gate and Lesson Curator gpt-5.4; independent evaluator
  gemini-3.8-flash. In the evaluator selection the chosen evaluator agreed with the author's pass/fail reference on
  25 of 30 items ([appendix/L05_evaluator_selection.md](appendix/L05_evaluator_selection.md)).
- Four pilot runs: natural 125 (full pipeline, 150-600 character body), long-form 125 (full pipeline, 1200-1500
  character target), defect 52 (52 long-form drafts, each as an unchanged original and a copy with one injected
  defect, 104 inputs), and mixed 125 (52 injected-defect drafts plus 73 unchanged drafts, revision path only).
- Every draft went through Gate, Critic, Optimizer and Gate at least once; a second cycle ran only if needed.
- Quality: the evaluator scored persona fit, clarity, actionability and factual grounding from 1 to 5; low quality
  means any dimension below 3.
- Registration: none. All four runs are exploratory pilots; the Study D thresholds were applied after the runs.

### Results
| Pilot run | Completed | Production-cost CV | Low quality, initial -> final | New cost, USD |
|---|---|---|---|---|
| Natural 125 | 125/125 | 0.148 | 2 -> 1 | 17.475105 |
| Long-form 125 | 125/125 | 0.069 | 3 -> 1 | 19.360275 |
| Defect 52, unchanged originals | 104/104 inputs (both arms) | not computed | 1 -> 2 | 6.200308 (both arms) |
| Defect 52, injected defects | (included above) | not computed | 52 -> 0 | (included above) |
| Mixed 125 | 125/125 | undetermined (0.168 known usage only; 2.328 with reservations) | 55 -> 1 | 11.060256 |

Source: `private/pilot125_v1/hypothesis_estimates.json`, `private/long125_v2/hypothesis_estimates.json`,
`private/defect52_v1/analysis.json`, `private/mixed125_v1/analysis.json` (costs: the result reports
`187_REAL_WORKFLOW_PILOT125_RESULTS.md`, `199_LONG125_V2_EXECUTION_RESULTS.md`,
`204_CONTROLLED_DEFECT52_RESULTS.md`, `207_MIXED125_HYPOTHESES_RESULTS.md`)

### Problems found
- Natural drafts were rarely low quality (2 in the natural run, 3 in the long-form run), below the 10-event minimum,
  so H3 was left inconclusive in both runs.
- In the defect test one unchanged original got worse after revision (1 -> 2 low quality), and the Gate passed both
  texts that the evaluator still rated low.
- In the mixed run, rate limits and an exhausted provider balance left 43 failed or unconfirmed attempts and USD
  3.914377 of production usage unconfirmed, so H2 could not be decided.
- The evaluator missed 5 of the 20 texts the author judged as failing.

### What changed next
- The final design ([AsPredicted #310130 text](ASPREDICTED_310130_SERVER_TEXT_2026-09-17.md)) keeps a natural
  condition and adds a mixed condition built from the same 125 Writer drafts: 52 drafts with fixed injected defects
  (13 per type) and 73 unchanged.
- Cost ledger rule frozen: unknown costs are never set to zero and are kept separate from budget reservations; if
  production usage is unknown, H2 is reported as undetermined.

The model selection history is in [appendix/L07_model_selection_history.md](appendix/L07_model_selection_history.md).
