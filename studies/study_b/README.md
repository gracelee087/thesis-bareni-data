# Study B — summary

> This summary was added on 2026-10-16 for the thesis appendix. It is a short description of a historical development study; it is not part of the final evidence (STUDY-E-1).

## What was tried

Can the Marketing department, built as a multi-agent pipeline with a refinement loop and batch lessons, reliably
and at a predictable cost write LinkedIn posts from topics derived from collected public creator posts? The final
B2 run (`b2_final_2026_terra_n125/`) tested H1 (completion), H2 (cost predictability) and H3 (fewer low-quality
outputs after refinement). It followed several excluded pilots.

## Method

- 125 tasks (`SB2F-001`–`SB2F-125`) in four batches of 31/31/31/32, 2026-08-15 to 2026-08-18.
- Before each batch, one Apify run collected public posts from a frozen 20-creator panel; a curation model kept
  only an abstract theme retargeted to the case company.
- Models: Claude Haiku 4.5 for curation, planner, researcher, writer, critic and lesson extraction; Claude Sonnet 5
  for the optimizer; GPT-5.6 Terra (low reasoning effort) as the judge.
- Revision rule: Critic -> Optimizer -> fresh judge runs only if a dimension is below 3/5, a critical violation is
  found, or the text is outside 1–100 words; at most two revision passes.
- Quality: the same judge's initial and final scores; low quality = any of four dimensions below 3/5.
- Batch lessons: at most three new lessons per batch, at most three injected per later task.
- Registered as AsPredicted #306768 on 2026-08-15, before the first paid call.

## Results

| Measure | Value |
|---|---|
| Completed tasks (H1, criterion >= 90%) | 125/125 — PASS |
| Tasks with 0 / 1 / 2 revision passes | 70 / 48 / 7 |
| Total LLM cost (USD, billing-verified) | 7.484791 |
| Per-task LLM cost CV (H2, criterion < 0.25) | 0.415 — FAIL |
| Low-quality outputs, initial -> final (H3, criterion >= 30% reduction) | 54 -> 2 — PASS |
| Technical failures | 0 |

Source: `b2_final_2026_terra_n125/data/analysis/final_analysis_billing_verified.json`

## Problems found

- Per-task cost fell into three separate levels by revision count (0, 1 or 2 passes), so cost variation was
  driven by the revision decision and H2 failed.
- The judge that decided whether to revise (GPT-5.6 Terra) also produced the initial and final scores used for H3,
  so the H3 result was not independent of the gate.
- The Apify cost in the sealed analysis (USD 7.3062) was later corrected to USD 7.5462
  (`b2_final_2026_terra_n125/data/analysis/apify_cost_errata_2026-08-24.json`); Apify cost is not part of H2.

## What changed next

- In Study C, the production gate and the independent evaluator are different models (`judge_gate` and
  `judge_eval` in `../study_c/config/models.json`).
- From Study C on, creator post collection with Apify was dropped and the author specified the topics
  (`../study_c/00_CANONICAL_PLAN_DECISION_2026-08-29.md`, section 3.2). The stated reasons were construct validity
  and a clear H2 cost boundary; removing personal-data processing was noted as a side effect.

## Privacy

The collected post texts, the creator list and creator identifiers are not published. Creator addresses in
published code and tests are replaced by meaningless placeholders.

---

## Original folder catalog (unchanged)


## Independent current experiment

- `b2_pilot_v0_8_terra/` is the active, self-contained Study B2 v0.8 pilot.
  It uses a frozen raw snapshot, fresh Haiku curation/generation, Terra judging,
  and conditional Sonnet repair. It imports no historical experiment package.
- `b2_openrouter_arm_a/` is the preserved engineering smoke prototype that preceded
  v0.8. Its receipts and data are not v0.8 inputs.

## Historical path-frozen experiments

| Experiment | Documents | Code prefix | Config prefix | Data root |
|---|---|---|---|---|
| B1 restart | `study_b/b1_*` | `code/bareni_pipeline/study_b_*` | `code/config/study_b1_*` | `data/study_b/b1*` |
| B2 v0.4 | `study_b/b2_*v0.4*` | `code/bareni_pipeline/study_b2_v04_*` | `code/config/study_b2_v04_*` | `data/study_b/b2_pilot_v0.4/` |
| B2 v0.5 | `study_b/b2_*v0.5*` | `code/bareni_pipeline/study_b2_v05_*` | `code/config/study_b2_v05_*` | `data/study_b/b2_pilot_v0.5/` |
| B2 v0.6 | `study_b/b2_*v0.6*` | `code/bareni_pipeline/study_b2_v06_*` | `code/config/study_b2_v06_*` | `data/study_b/b2_pilot_v0.6/` |
| B2 v0.7 | `study_b/b2_*v0.7*` | `code/bareni_pipeline/study_b2_v07_*` | `code/config/study_b2_v07_*` | `data/study_b/b2_pilot_v0.7/` |

Historical files remain at their frozen paths because old execution manifests
hash those exact locations. Moving them without a compatibility layer would make
the completed experiments fail their own reproducibility checks.
