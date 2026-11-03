# Study A — summary

> This summary was added on 2026-10-16 for the thesis appendix. It is a short description of a historical development study; it is not part of the final evidence (STUDY-E-1).

## What was tried
Study A developed the single-task Marketing pipeline through Pilots 7 (v0.7), 8 (v0.8) and 10 (v0.9) and prepared a 125-task confirmatory run (`CFM-001`–`CFM-125`). Pilot 10 was a full-scale dress rehearsal of the unchanged pipeline v0.9, run because its conditional optimizer branch had never run live at scale.

## Method
- Pilot 10: 125 new briefs `P10-001`–`P10-125` in fixed order, 5 strata of 25 (75 informational, 50 purchase); cost cap USD 15.
- Roles and models (from the run records): planner, researcher, writer and optimizer `claude-sonnet-5`; router judge and outcome judge `gpt-5.6-terra`.
- Routing: the router judge decides whether to revise; at most one optimizer revision. No critic, reflector or auditor.
- Quality: the outcome judge scores the single-pass and final texts blind; low quality = failing the gate (total below 16/20, any of four dimensions below 3/5, or a critical violation).
- Memory: a new empty lesson store for every task (`reset_per_task`); no lesson transferred between tasks. Pilot 8 used the same rule; Pilot 7 kept memory within 30-task cohorts.
- Registration: none. Pilot 10 is exploratory and excluded from H1–H3.

## Results
| Pilot 10 measure | Value |
|---|---|
| Completed tasks | 125 / 125 |
| Tasks revised by the optimizer | 12 |
| Production-cost CV (threshold < 0.25) | 0.177 |
| Low-quality outputs, single pass -> final | 16 -> 9 (reduction 0.4375) |
| Production cost, total (USD) | 8.19933 |
| Full recorded cost incl. outcome judge (USD) | 10.8929838 |

Source: `../../data/pilot10/analysis/pilot10_exploratory_v0.1.json`

## Problems found
- Memory was reset for every task, so the pipeline could not carry a lesson from one task to the next; the confirmatory plan was limited to a frozen 125-task workload and was not allowed to claim longitudinal learning.
- The revision branch ran on only 12 of 125 tasks.
- The 125-task confirmatory plan was superseded on 2026-08-11 before approval or freeze: 0 confirmatory records, 0 paid confirmatory calls.

## What changed next
- Study B2 N=125 was chosen as the only planned final H1–H3 evaluation.
- B2 requires 125 new briefs (the CFM bank is kept only as an exclusion bank), four controlled sequential batches, cost and time caps, and a new hash manifest.

The original Study A files stay at their historical paths (table below).

---

## Original folder catalog (unchanged)


Study A's completed experiments predate the unified `studies/` layout. Their
frozen manifests contain repository-relative paths, so the original files remain
in place until a compatibility-preserving migration is completed.

| Experiment | Protocol/review documents | Code prefix | Config prefix | Data root |
|---|---|---|---|---|
| Pilot 7 | `pilot7/` | `code/bareni_pipeline/pilot7*` | `code/config/pilot7*` | `data/pilot7/` |
| Pilot 8 | `pilot8/` | `code/bareni_pipeline/pilot8*` | `code/config/pilot8*` | `data/pilot8/` |
| Pilot 10 | `pilot10/` | `code/bareni_pipeline/pilot10*` | `code/config/pilot10*` | `data/pilot10/` |
| Final acceptance | `final_acceptance/` | `code/bareni_pipeline/final_acceptance*` | `code/config/final_acceptance*` | `data/final_acceptance/` |
| Final confirmatory | `final_confirmatory/` | `code/bareni_pipeline/confirmatory*` | `code/config/final_confirmatory*` | `data/final_confirmatory/` |

These are historical, path-frozen artifacts. New Study A experiments must put
all five categories inside one experiment directory under `studies/study_a/`.
