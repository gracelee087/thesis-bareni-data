# Study C — summary

> This summary was added on 2026-10-16 for the thesis appendix. It is a short description of a historical development study; it is not part of the final evidence (STUDY-E-1).

## What was tried
Study C tried to remove the circularity of the predecessor study, where one judge both opened the
revision gate and measured quality. The runtime gate judge and a blinded outcome judge were separated
by exact model and provider, and a calibration pilot was meant to estimate how often first drafts are
low quality, so that the final sample size could be derived from that rate.

## Method
- Topic bank of 100 owner-written topics, split by a fixed seed into fixture 9 / calibration 32 / final 59.
- Calibration batch 1 only: 16 tasks (`SC-001`–`SC-016`), run 2026-08-29.
- Models: planner, researcher, writer, critic, optimizer, lesson extractor and gate judge all
  `gemini-3.7-flash`; blinded outcome judge `claude-opus-5`.
- Routing: revise only when the gate judge fails the draft; stop on gate pass, no improvement,
  per-task cost ceiling (USD 0.25) or 6 revisions.
- Quality: the blinded judge scored the initial and final text; low quality = any of 4 dimensions below 3/5.
- Defect injection: 8 calibration texts (`SC-001`–`SC-008`) each given 4 defect types
  (fabricated evidence, wrong persona, no actionable step, incoherent) = 32 defective texts, scored by both judges.
- Not registered; the final stage was never run.

## Results
| Measure | Value |
|---|---|
| Tasks complete | 16 / 16 |
| Gate pass on first draft | 16 / 16 (total 20/20 on 15 tasks, 18/20 on 1) |
| Revisions made | 0 |
| Blinded judge total score (out of 20) | 13 to 18 |
| Low quality, initial -> final (blinded judge) | 0 -> 0 |
| Production cost, sum / CV | USD 0.21548475 / 0.004 |
| Measurement cost, sum | USD 2.842725 |
| Total cost, sum | USD 3.05820975 |
| Defect texts scored below 3 on some dimension | blinded 28 / 32, gate 28 / 32 |
| "No actionable step" defect caught | blinded 4 / 8, gate 4 / 8 |
| Defect-injection spend | USD 3.35843375 |

Source: `data/runs/` (16 task records) and `data/judge_validation/defect_injection.json`

## Problems found
- The gate judge passed every draft, so the revision path never ran and there was nothing to compare.
- The blinded judge found 0 low-quality first drafts, so the planned low-quality reduction could not be measured
  and the sample-size rule (which needs this rate) had no input. The gate and blinded judges also disagreed
  strongly on the same texts (gate mostly 20/20, blinded 13 to 18).
- Both judges could score below 3 on clearly broken text, but missed half of the "no actionable step" defects.
- The lesson-extractor call failed with HTTP 404 (`model: gemini-3.7-flash` not found), so batch 1 closed
  without a memory update.
- Measurement cost was about 13 times production cost.
- Three incompatible planning documents existed at once; two were marked superseded on 2026-08-29.

## What changed next
- Study D chose its judges with a 40-item judge test (20 clean texts and 20 deliberately damaged texts).
- Study D replaced the gate judge with `gpt-5.6-luna`, a model outside the generation path.
- Study D adopted the route in which every draft receives at least one Critic -> Optimizer revision, with the gate
  deciding only on a second revision.
