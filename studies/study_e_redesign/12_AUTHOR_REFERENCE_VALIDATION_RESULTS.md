# Study E Author Reference Rating Validation

## Status and audit boundary

- The first rating round was frozen and pushed in commit `d38e0fb` before the rerating packet was opened.
- The immediate rerating was frozen and pushed in commit `c36e56b` before the private mapping and intended construction labels were inspected.
- First-round raw record: `10_AUTHOR_RATING_ROUND1_RAW.md`, SHA-256 `f40aa3954e9589ef63e626d8ad915aa1209b29181292243847c22fcf89266fce`.
- Immediate-rerating raw record: `11_AUTHOR_RATING_RERATE_RAW.md`, SHA-256 `7994b1b2f0a6a457786b78dbd45bfbb37317a6a031127a002968a057b86f9ee7`.
- The comparisons below were calculated only after both raw records had been frozen.

## 1. Immediate intrarater consistency

The ten-item rerating sample contained three normal, three subtle-defect, and four critical-defect items under new IDs and a new order.

| Rerating ID | First-round ID | Pass/fail | Critical violation | PF | CL | AC | FG |
|---|---|---:|---:|---:|---:|---:|---:|
| EVAL-RERATE-001 | EVAL-BLIND-027 | same | same | same | same | same | same |
| EVAL-RERATE-002 | EVAL-BLIND-004 | same | same | same | same | same | same |
| EVAL-RERATE-003 | EVAL-BLIND-028 | same | same | same | same | same | same |
| EVAL-RERATE-004 | EVAL-BLIND-029 | same | same | same | same | same | same |
| EVAL-RERATE-005 | EVAL-BLIND-003 | same | same | same | same | same | same |
| EVAL-RERATE-006 | EVAL-BLIND-022 | same | same | same | same | same | same |
| EVAL-RERATE-007 | EVAL-BLIND-015 | same | same | same | same | same | same |
| EVAL-RERATE-008 | EVAL-BLIND-012 | same | same | same | same | same | same |
| EVAL-RERATE-009 | EVAL-BLIND-017 | same | same | same | same | same | same |
| EVAL-RERATE-010 | EVAL-BLIND-026 | same | same | same | same | same | same |

- Pass/fail exact agreement: **10/10 (100%)**; Cohen's κ = **1.00**.
- Critical-violation exact agreement: **10/10 (100%)**; Cohen's κ = **1.00**.
- Exact agreement across the four 1–5 scores: **40/40 (100%)**.
- Entire four-score vector reproduced exactly: **10/10 items**.

## 2. Agreement with the constructed item targets

These are construction-target checks, not comparisons with an independent external gold standard.

| Constructed item kind | N | Author pass | Author noncritical fail | Author critical fail | Intended pass/fail agreement | Intended critical-status agreement |
|---|---:|---:|---:|---:|---:|---:|
| Normal approved source | 10 | 10 | 0 | 0 | 10/10 | 10/10 |
| Subtle single-defect variant | 10 | 0 | 10 | 0 | 10/10 | 10/10 |
| Critical single-defect variant | 10 | 0 | 0 | 10 | 10/10 | 10/10 |
| **Total** | **30** | **10** | **10** | **10** | **30/30** | **30/30** |

For detecting author-rated low-quality items against normal items:

- False negatives: **0/20**.
- False positives: **0/10**.
- Sensitivity: **20/20 (100%)**.
- Specificity: **10/10 (100%)**.

For detecting constructed critical violations:

- Critical misses: **0/10**.
- Noncritical items incorrectly marked critical: **0/20**.
- Critical sensitivity: **10/10 (100%)**.
- Critical specificity: **20/20 (100%)**.

Each subtle variant was designed to lower one named dimension to 2. The author assigned score 2 to that intended target dimension in **10/10** cases: Persona Fit 2/2, Clarity 2/2, Actionability 3/3, and Factual Grounding 3/3.

## 3. Interpretation

The results support using these ratings as a stable **single-author reference** for the formative evaluator-selection exercise. They show that the author applied the frozen rubric consistently over the immediate rerating interval and that the constructed items behaved as designed.

They do not establish a universal human gold standard, population prevalence, or external validity. The same author approved the normal sources and later rated the blinded variants; the rerating was immediate and may retain memory; and the injected defects were deliberately constructed rather than naturally sampled. Accordingly, Study E must report agreement with the **author reference rating**, not human consensus or objective truth.

## 4. Next decision

The author-reference set is ready for the three candidate evaluators. Each candidate will rate the same 30 items once under the frozen prompt and schema. Model outputs must remain hidden from the author until all 90 calls are complete. Candidate comparison follows the registered priority: critical misses, all false negatives, false positives, schema failures, cost, then latency; the four dimension scores are secondary descriptive results.
