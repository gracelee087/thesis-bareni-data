> English translation prepared 2026-09-17 of `RESULTS_FINAL_EXPERIMENT_1_20260908.md`. The Korean original is the recorded/frozen document; where wording differs, the original governs.

# STUDY-E-1 Final Experiment — Results for Verification and Submission

The subject is the **STUDY-E-1 final experiment**, and the raw-data path is `private/final125_v1`. All 1,860 calls started on 2026-09-08. Started at 14:08:53 German time, ended normally at 15:52:11. Production and independent evaluation of the 125 natural tasks and the 125 mixed tasks using the same original drafts were completed.

## Analysis Scope

The linkage between the registration receipt and the frozen/operational-patch hashes was verified. Re-querying the registration web page this time was refused with HTTP 406, so completion of an external re-query is not claimed. The rationale for selecting the analysis target is stated in the methodology record below.

Because the two conditions share the same 125 original tasks, they are not pooled as an independent N=250. The mixed condition consists of 52 transformed and 73 unchanged original drafts and is analyzed separately. Only the planned Proposal-scope H1–H3, descriptive statistics for quality, cost, latency, and body-text metrics, and the total-score Wilcoxon were computed.

## H1–H3 and Total Score

| Item | Natural condition | Mixed condition |
|---|---:|---:|
| H1 completion rate (≥90%) | 125/125, 100% — met | 125/125, 100% — met |
| H2 production-cost CV (<0.25) | 0.06375145 — met | 0.12753798 — met |
| H3 low quality initial→final | 1→0 | 52→1 |
| H3 relative reduction (≥30%) | 100% — met | 98.076923% — met |
| Valid evaluation pairs / missing | 125 / 0 | 125 / 0 |
| Mean total score (out of 20) | 19.728→19.664 | 15.384→19.704 |
| Total-score two-sided Pratt Wilcoxon p | 0.622644532331 | 6.80539900601e-10 |

H1 is technical production completion and differs from passing the quality criterion in independent evaluation. H2 is the sample standard deviation/mean of per-task production cost. Natural includes full production and the Curator apportioned equally within each batch; mixed includes the new Gate/Critic/Optimizer and retries; independent-evaluation cost is excluded.

H3 low quality is the case where any one score among persona fit, clarity, actionability, and factual grounding is below 3. The natural (1−0)/1=100% reduction is an observed value from a single initial event and is therefore not interpreted as strong generalization or confirmation of population-level improvement. Natural N043's scores were [2,3,4,4]→[3,4,5,5]. The mean total score fell slightly from 19.728→19.664, and Wilcoxon p=.622645 is not a significant total-score change.

In mixed, all 52 initial low-quality cases escaped low quality, but unchanged M032 (original N082) became newly low quality at [3,4,4,5]→[2,3,4,5], so the net reduction is 51/52=98.076923%. Total score rose from 15.384→19.704. The fixed test was applied: two-sided α=.05, Pratt zero handling, asymptotic computation, no continuity correction. The Wilcoxon does not test the 30% boundary of H3. Limitations remain regarding dependence on the AI evaluator and batch memory, score ceiling effects, and the artificial-defect condition.

## Costs and Failed Calls

| Scope | Usage-based cost USD |
|---|---:|
| Natural production, including Curator | 17.35502475 |
| Natural independent evaluation | 1.97852175 |
| Mixed new production | 5.04817710 |
| Mixed independent evaluation | 2.24584950 |
| Total | **26.62757310** |

Cap USD49.99. 1,856 successes, 4 response validation failures. The failures were the first attempts of the N069/N099/N101/N107 Planner, all of which subsequently succeeded. The failure cost total of USD0.037459 is also included in the total above. Transport failures, HTTP errors, missing responses, unknown usage/cost, and unresolved failures are 0.

| Provider | Attempts | Usage-based USD | Actual billing reconciliation |
|---|---:|---:|---|
| anthropic | 254 | 11.76853900 | Awaiting evidence |
| google | 459 | 4.22437125 | Awaiting evidence |
| openai | 1147 | 10.63466285 | Awaiting evidence |

Raw-response tokens × frozen rates and the Langfuse server-stored costs all match. This is separate from reconciliation of provider taxes, credits, discounts, and monthly invoices. Reconciliation targets were prepared in `provider_reconciliation.csv` and the per-request `attempt_costs_1860.csv`. Billing-administrator credentials, a connected browser session, and provider billing records corresponding to this execution have not currently been obtained. The existing cost screen from September 7 was not used as billing evidence for the new September 8 execution.

## Descriptive Statistics by Quality Dimension

Mean initial→final. All cells n=125, 0 missing. Full distributions and paired changes are in the analysis JSON and `quality_descriptive.csv`.

| Dimension | Natural | Mixed |
|---|---:|---:|
| persona_fit | 4.784→4.776 | 3.448→4.800 |
| clarity | 4.968→4.904 | 3.904→4.936 |
| actionability | 4.984→4.984 | 3.960→4.984 |
| factual_grounding | 4.992→5.000 | 4.072→4.984 |

## Full Verification

- Registration/freeze/permitted-recovery linkage and 81 frozen files, SDK versions confirmed.
- Hashes of 3,972 report inputs match the output manifest.
- 1,860 start/result pairs, request and parent-response hashes, full recomputation of usage and cost.
- Linkage of Planner/Researcher/Writer/revision/Gate/independent-evaluation outputs for 250 tasks and confirmation of the first-revision and at-most-twice rule.
- Reproduction of 52 mixed transformations, comparison of 73 unchanged originals and upstream reuse.
- Independent check of natural and mixed H2 CV and H3 raw scores with the same Wilcoxon formula.
- Verification of evaluation reuse for exactly identical title/body in 25 natural and 16 mixed cases. New successful evaluator calls are 459, and valid initial/final pairs are 250.
- Natural revisions once 120 / twice 5; mixed once 124 / twice 1. Natural Curator 4 runs, mixed new Curator 0.
- Full reconciliation of 254 traces/1,860 generations in the Langfuse `study-e-record` project. Inputs, outputs, models, statuses, error levels, tokens, and costs match; 0 missing/extra/mismatched. A rate limit on separate read requests was resolved by paging and waiting, with 0 additional model calls.
- 7 existing tests of the analysis/reporter passed. 0 modifications of frozen experiment/analysis source, original text, or scores.

The operational branch of the final Gate is release_candidate for all 250. This does not mean that all independent evaluations passed, and mixed M032's final low-quality verdict was preserved as is. The 150–2000-character hard range for bodies is fully met. For the 1200–1500-character target range, the counts are natural initial103/final89 and mixed initial82/final86; target deviations were neither hidden nor regenerated.

## Submission Status

Experiment, analysis, local integrity, full Langfuse reconciliation, and preparation of the results supplement are complete. Actual provider billing reconciliation, confirmation of the final submission venue/format, full manuscript integration, public GitHub/Zenodo release and DOI, and actual submission receipt are not complete. Neither local ZIP generation nor meeting the H1–H3 criteria is marked as "thesis submission complete". This document is a verified Study E results supplement and does not replace the full manuscript.

Key evidence: `reports_final_2026-09-08/{natural_analysis.json,mixed_analysis.json,integrity_audit.json,submission_checks.json,report_manifest.json,cloud_audit/receipt.json}`. 500 rows of body metrics, activity ledgers of 125 rows each for natural/mixed, per-role and per-batch costs, latency descriptive statistics, failure/usage ledgers, and server evidence were preserved together.

## Methodology Record: Selection of the Analysis Target

STUDY-E-1 took as its analysis target the data re-executed under the same frozen protocol after the missing cost/usage records and the results of the preceding execution were confirmed. The preceding data and results are preserved separately in `private/final125_prior_execution_2026-09-08/` and `RESULTS_310130.md`. The name STUDY-E-1 is a study identifier and does not denote a first execution or a new preregistration.
