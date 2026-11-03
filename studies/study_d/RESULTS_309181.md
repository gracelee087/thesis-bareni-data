# Study D — Re-registered Final (AsPredicted #309181) — Confirmatory Results

Generated 2026-09-01 from `data/analysis/final_analysis.json` (schema `b2-final-analysis-v2-recovery-safe`),
125 TaskRecords `SD-416`–`SD-540`, four `CLOSED` batch receipts. Registration:
https://aspredicted.org/fz2fb2.pdf (2026-09-01 08:13 UTC). Frozen manifest roll-up
`b75de17cd5e1a4fb8cad6a9ceb82afac0a6bb195f72534f2cfbb143feff81aed`; source tree
`5b25cb3590be9a850ab5306e41f3301f8c44b7834b3797edd27b2440b55078ae` (unchanged throughout; no
runtime patch was needed). Execution 2026-09-01 10:16–13:56 local (Europe/Berlin), all four
batches in sequence in one day.

## Preregistered verdicts

| Hypothesis | Preregistered criterion | Observed | 95% CI | Verdict |
|---|---|---|---|---|
| H1 completion | ≥ .90 | 125/125 = 1.000 | Wilson [0.970, 1.000] | **PASS** |
| H2 production-cost CV | < .25 | CV = 0.1852 (mean USD 0.02578/task, total USD 3.2223) | bootstrap [0.1395, 0.2286] | **PASS** |
| H3 blinded low-quality reduction | ≥ .30 (≥10 initial events) | 18 → 0 = 1.00 | paired bootstrap [1.000, 1.000] | **PASS** |

- H3 paired transitions (blinded evaluator, N=125, missing pairs 0): not-low→not-low 107, low→not-low 18, not-low→low 0, low→low 0. Exact McNemar two-sided p = 7.63e-06; paired-total Wilcoxon (Pratt) p = 1.31e-10.
- Gate-judge contrast (circular, never the verdict): 23 → 0.
- Blinded totals (4–20): mean 14.46 → 15.58; per task up 78 / same 30 / down 17.
- Refinement: every task received one Critic→Optimizer pass; 4 tasks needed a second (129 passes total). Mean production cost by refinement count: 1 pass USD 0.0252 (n=121), 2 passes USD 0.0421 (n=4).
- Final body length 150–600 characters: 125/125.

## Cost (USD, frozen prices verified online 2026-09-01)

| Scope | USD |
|---|---|
| H2 production (generation, routing gates, Critic/Optimizer, lesson extraction) | 3.2223 |
| Blinded measurement (claude-opus-5, outside H2) | 25.8818 |
| Total observed | 29.1041 |
| By provider — Anthropic / Google / OpenAI | 25.8818 / 2.5332 / 0.6891 |

Langfuse reconciliation: 1,171 generations since batch 1 start, USD 29.104055 recorded = local
ledger USD 29.104055 (tasks 29.091143 + lesson closes 0.012912). Budget-pause receipts 0;
recoverable incomplete attempts 0; cap USD 100 never approached.

## Operational recovery events (all automatic, all inside complete records)

28 failed provider attempts across the 125 tasks, every one recovered by the registered
retry policy before the task completed: critic ServerError x4; judge_eval_final SchemaInvalid x1; judge_gate_final SchemaInvalid x1; optimizer OutputTruncated x17; optimizer ServerError x5. Billed cost of failed attempts USD 0.2503
(retained in H2/measurement ledgers). Lesson extraction: 2 schema-invalid attempts
(batch 3 and batch 4, lesson text over the 240-character limit) each retried to success. No task was halted, no budget
pause, no runtime patch, no manual intervention after launch.

## Cross-batch memory trajectory (descriptive only)

| Batch | Lessons at start | Ops after batch | Active after | Tasks selecting ≥1 lesson | Mean initial blinded total | Initial low | Mean production USD |
|---|---|---|---|---|---|---|---|
| 1 | 0 | ADD 1 / MERGE 0 / SKIP 0 | 1 | 0/31 | 14.42 | 3 | 0.0249 |
| 2 | 1 | ADD 2 / MERGE 1 / SKIP 0 | 3 | 31/31 | 14.58 | 6 | 0.0264 |
| 3 | 3 | ADD 1 / MERGE 1 / SKIP 0 | 4 | 31/31 | 14.58 | 6 | 0.0264 |
| 4 | 4 | ADD 0 / MERGE 1 / SKIP 0 | 4 | 32/32 | 14.28 | 3 | 0.0250 |

Final register (4 lessons, cap 12):

- `SD-B1-L01` (source batches [1, 2, 3, 4], selected by 91 tasks): Anchor all advice in source evidence. Avoid fabricating numerical thresholds (e.g., time limits) or using jargon. Use practical, diagnostic language tailored to a 1–10 person business owner.
- `SD-B2-L01` (source batches [2], selected by 0 tasks): Explicitly decline all requests related to high-sensitivity legal work or legal advice. Direct automation efforts exclusively toward non-legal business operations.
- `SD-B2-L02` (source batches [2], selected by 50 tasks): Anchor all business policies in mandated human-in-the-loop protocols for money movement and high-risk decisions. Avoid inventing live system capabilities or proprietary alert mechanisms.
- `SD-B3-L01` (source batches [3], selected by 32 tasks): Strictly adhere to the mandatory No-CTA rule. Do not include promotional calls to action, invitations for diagnostic calls, or external service prompts.

Interpretation boundary (preregistered): batches differ in topics and Planner selects lessons
by judged relevance, so neither the across-batch column nor the selected/unselected contrast
identifies a causal memory effect.

## Descriptive text statistics (initial → final)

Words 78.4 → 68.3; Flesch Reading Ease
46.7 → 47.1; Flesch-Kincaid grade
10.2 → 10.3; TTR
0.815 → 0.873. Median task latency 97.3 s.

## Deviations and disclosures

1. Critic/Optimizer model: gemini-3.6-flash replaced gemini-3.7-flash before registration
   after two paid live smokes and probes returned HTTP 503 on every gemini-3.7-flash call
   (disclosed in the registration; fixer ablation recorded in `config/models.json`).
2. All four batches ran consecutively on one day (registration fixed order, not dates).
3. The detached runner script (`tools/run_all_batches.ps1`) failed to capture the CLI's
   stdout into its log; batch closes, telemetry receipts and JSON records are complete and
   are the evidence. Cosmetic only.
4. Pre-registration paid calls on 2026-09-01 (three smokes USD 0.453, fixer ablation USD
   2.217) are excluded design/engineering costs and enter no hypothesis.
5. The preregistered floor of ten initial low-quality events was met (18), so H3 carries a
   criterion decision rather than an inconclusive result.
6. Post-hoc re-verification (2026-09-01, read-only): every H1/H2/H3 statistic, cost total, provider
   split, transition table, refinement count and frozen-file hash was recomputed from the raw
   TaskRecords and matched the sealed values exactly; 50/50 tests pass. One documentation
   inconsistency was found in `config/pricing.json` (frozen, not edited): its
   `online_verification_2026_09_01` note says OpenAI publishes no cache-write charge, but the
   Responses API reported `cache_write_tokens` on all 255 gpt-5.6-luna calls and OpenAI's pricing
   page lists short-context cache writes at USD 0.25/M for gpt-5.6-luna. The ledger billed those
   tokens at 0.25/M, which is the correct rate; only the note sentence is wrong. No number changes.
