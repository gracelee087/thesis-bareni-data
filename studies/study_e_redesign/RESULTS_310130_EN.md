> English translation prepared 2026-11-10 of `RESULTS_310130.md`. The Korean original is the recorded/frozen document (SHA-256 `cde70ceeac565305a6c111ec678e7812871e6ad776828d8d88dfce4f782414a7`, listed in `studies/study_e_ablaton/private/FREEZE.json`); where wording differs, the original governs. The relative links of the original are rendered here as plain paths; `private/final125_prior_execution_2026-09-08/` is not included in the public repository.

> **This report is the result of the preceding completed execution.** At the author's request on 2026-09-08, a separate new execution was started, and these figures are not used as the results of the new execution. The raw data of the preceding execution were preserved in `private/final125_prior_execution_2026-09-08/`.

# Study E Final Empirical Test — AsPredicted #310130 Results

Analysis date: 2026-09-08. **Experiment execution, independent evaluation, pre-specified local analysis and raw-data integrity verification completed. The natural-condition H2 cannot be decided because usage is unconfirmed.** Manuscript integration, provider invoice reconciliation, full Langfuse ingestion reconciliation and public release are separate tasks.

Basis: registration receipt (`private/final125_v1/registration.json`), frozen protocol (`215_FINAL_EXPERIMENT_PROTOCOL_DRAFT.md`), Proposal scope decision (`219_PROPOSAL_ONLY_ANALYSIS_DECISION.md`). The local registration record is #310130, 2026-09-07 15:03:04 UTC, which precedes the first call. The registration text is at <https://aspredicted.org/310130>. The external registration server was not queried again in this analysis. Document 215, whose title still contains 'draft', is subject to the frozen hash and was not modified.

## 1. Main results

| Item | Natural condition | Mixed condition |
|---|---:|---:|
| Scheduled tasks | 125 | 125 |
| H1 technical production completion rate, criterion ≥90% | **125/125, 100%, met** | **125/125, 100%, met** |
| Independent-evaluation initial and final valid pairs | 125/125, missing 0 | 125/125, missing 0 |
| H2 production-cost CV, criterion <0.25 | **undetermined: production usage unknown for 2 calls** | **0.124440, met** |
| Initial → final low quality | **1 → 2** | **51 → 1** |
| H3 relative reduction (B−F)/B, criterion ≥30% | **−100%, not met** | **98.0392%, met** |
| Mean total score, out of 20 | 19.624 → 19.400 | 15.360 → 19.656 |
| Mean paired difference in total score | −0.224 | +4.296 |
| Wilcoxon statistic for total score | 763.5 | 721.5 |
| Two-sided Wilcoxon p for total score | 0.0102299286875 | 1.38748357252×10⁻¹⁰ |

H1 is a criterion about whether production was completed within the fixed recovery and budget rules. It does not mean that every attempt ended without error or that every text passed the quality criteria. H3 low quality means that at least one of the four dimensions is below 3 points.

In the natural condition, initial low quality was very rare at 1 case, and the scores were close to the maximum. The 1 initial low-quality case was still low quality at the final stage, and 1 other case was newly judged low quality. −100% means that the number of low-quality cases rose from 1 to 2; it does not mean that the quality of all texts worsened by 100%. The observed H3 criterion is not met. The denominator was not changed and the decision was not removed on the grounds that initial events were few.

In the mixed condition, all 51 initial low-quality cases left low quality at the final stage, but 1 initially non-low-quality case was judged low quality at the final stage, so the net reduction is 50/51. The fact that 52 defects were injected was not taken to mean 52 initial low-quality cases. The remaining 73 are not 'normal texts' but 'unchanged first drafts'.

The two conditions share the same 125 first drafts. They are not pooled as an independent N=250, and the cost difference between full natural production and the mixed revision path is not interpreted as a causal cost-saving effect for the same work.

Wilcoxon is a two-sided signed-rank test of the total score and does not test the 30% boundary of H3. In the natural condition the mean total score fell. p<.05 must not be used as evidence of improvement. Pratt zero handling, average ranks, the asymptotic method, no continuity correction and SciPy 1.17.1 were used. Limitations include batch-memory dependence, shared tasks, the assumption about the distribution of differences, and the fixed AI evaluator.

## 2. Costs and the reason H2 is undetermined

Unit USD. 'Confirmed cost' below is the value obtained by applying the frozen rates to the preserved usage; it is not the amount reconciled with provider invoices.

| Scope | Confirmed call cost | Reserved, usage unconfirmed |
|---|---:|---:|
| Natural production, including Curator | 17.88685450 | 0.29003700 |
| Natural independent evaluation | 2.18122545 | 0 |
| Mixed new production path | 5.12442690 | 0 |
| Mixed independent evaluation | 2.34687307 | 0.04062150 |
| Total | **27.53937992** | **0.33065850** |

The budget ledger total is **27.87003842** and the approved cap is 49.99. The reserved amounts are not actual costs, statistical upper or lower bounds of cost, or known zero dollars.

| Attempt with unconfirmed usage | Preserved error | Reserved USD | Effect on H2 |
|---|---|---:|---|
| SE-FINAL-N020_researcher__a001 | HTTP 400 / invalid_request_error | 0.2634000 | natural production cost unknown |
| SE-FINAL-N105_critic1__a001 | APIConnectionError | 0.0266370 | natural production cost unknown |
| SE-FINAL-M063_eval_final__a001 | ServerError | 0.0406215 | independent-evaluation cost, outside the mixed H2 scope |

All three calls succeeded in a subsequent call, but the usage of the successful retry does not establish the usage of the earlier failed attempt. The natural H2 is therefore left **undetermined**, neither failed nor passed. Nor should all 125 tasks, for which part of the cost is known, be read as 'no cost data at all'. The per-task total production cost descriptive statistics of the reporter were suppressed as not determinable, and the known parts remain in the O/X CSV and the per-role ledger.

The mixed H2 includes only the new Gate/Critic/Optimizer calls and their retry costs. Per task: mean 0.04099542, sample SD 0.00510148, median 0.04003125, 95th percentile 0.04492215, minimum 0.02477620, maximum 0.06889895. The existing natural Planner/Researcher/Writer costs and the independent-evaluation costs were not double-counted in the mixed production cost.

## 3. Quality descriptive statistics

Mean initial → final. Observations per cell 125, missing 0. Whole-sample SD, median, 95th percentile, range and paired-difference descriptive statistics are in the per-condition analysis JSON and `quality_descriptive.csv`.

| Dimension | Natural | Mixed |
|---|---:|---:|
| Persona fit | 4.696 → 4.592 | 3.400 → 4.784 |
| Clarity | 4.960 → 4.904 | 3.944 → 4.944 |
| Actionability | 4.968 → 4.904 | 3.952 → 4.928 |
| Factual grounding | 5.000 → 5.000 | 4.064 → 5.000 |
| Mean total ± sample SD | 19.624 ± 0.7584 → 19.400 ± 1.0999 | 15.360 ± 5.5189 → 19.656 ± 0.8529 |

Natural total-score changes: up 7 / same 98 / down 20; mixed: up 61 / same 53 / down 11. The final factual-grounding mean of 5 points is the judgment of this AI evaluator and is not a complete verification of actual factual accuracy.

The final low-quality records are natural `N016`, `N040` and mixed `M055`. The source of `M055` is `N040`, in the unchanged condition. For the same first text, the natural initial scores [2,4,3,5] and the mixed initial scores [4,5,4,5] differed. The actual measurement variation that arose in separate evaluation calls was preserved; neither score was copied to or corrected from the other. This case shows the uncertainty of fixed AI evaluation, and no additional agreement test was performed this time.

## 4. Body-text descriptive statistics

Mean initial → final. Title excluded; the frozen approximate rules for English words, sentences and syllables were used. All 500 initial/final bodies were recorded. Detailed distributions and paired differences are in the per-condition JSON and `text_descriptive.csv`; per-body values are in `text_metrics_500.csv`.

| Metric | Natural | Mixed |
|---|---:|---:|
| Flesch reading ease | 58.70604 → 58.63768 | 56.14386 → 58.84425 |
| Flesch-Kincaid grade | 9.61874 → 9.60208 | 9.78594 → 9.54330 |
| Word count | 228.456 → 243.128 | 223.008 → 238.688 |
| Lexical diversity, TTR | 0.63254 → 0.62149 | 0.64099 → 0.61941 |

The final bodies in both conditions fall within the hard range of 150–2000 characters. The counts within the 1200–1500-character target range are natural initial 96 / final 84 and mixed initial 84 / final 85. Target deviation was distinguished from hard-contract failure. Readability and TTR are surface text indicators and do not substitute for factuality or overall quality validity.

## 5. Latency and operating records

| Production time per task, seconds | Natural mean / median / 95th percentile | Mixed mean / median / 95th percentile |
|---|---:|---:|
| Sum of direct production call times | 65.213 / 61.648 / 97.129 | 7.339 / 6.847 / 11.510 |
| Elapsed time from first production call to production completion | 101.195 / 64.899 / 119.823 | 10.567 / 9.730 / 15.845 |

Observations 125 each, missing 0. The sum of call times includes direct production failures and retries and excludes independent evaluation and the batch Curator. Elapsed time includes waits and interruptions within a task. The natural maximum elapsed time of 2081.870 seconds was preserved as is. The latency distributions, SD and range of all attempts by role are in `latency_descriptive.csv`. Because the scope of work differs between the two paths, this is not interpreted as a simple speed-up factor.

- Execution ended: 2026-09-08 11:09:21 UTC / 13:09:21 Europe/Berlin. Final session `stop_reason=null`, both conditions 125/125.
- Natural 1144 + mixed 748 = **1892 API attempts**. 1866 succeeded, 23 validation failures, 3 transport failures. For all 26 failed attempts, a subsequent success of the same logical call was confirmed. Failure costs and errors were not removed.
- Natural semantic revision: once for 120 tasks / twice for 5; mixed: once for 123 / twice for 2. The first-revision path ran for every task.
- Evaluation reuse for exactly identical title and body: natural 24, mixed 10. The 250 valid evaluation pairs and the 466 distinct successful evaluator calls are different counts.
- Natural Curator 4 runs, mixed 0. The lesson-ledger count after each batch was 2 → 4 → 4 → 4. This alone does not claim a causal effect of the lessons.
- The operational recovery history, including the balance interruption of 7 September and the HTTP 400 equivalent, was retained. No re-registration, model change or additional quality regeneration was made.

## 6. Verification and outputs

**Verification passed:** 7 existing tests of the analysis/reporter, the link between the registration receipt and the frozen hashes and the permitted operational patches, 81 frozen files, library versions, 4036 analysis inputs unchanged, 1892 start/result pairs, request and parent-response hashes, cost recomputation for 1889 responses with usage, reproduction of the 52 mixed transformations and comparison of the 73 unchanged originals, upstream material reuse comparison, direct recomputation of H3 raw scores, independent check of the same Pratt Wilcoxon formula, mixed H2 CV check, session cost total comparison.

The analysis reporter CLI raised a cp1252 UnicodeEncodeError at the step of printing a Korean path to the console after writing all files and the manifest. The saved JSON/CSV were parsed and the output hashes in the manifest were verified separately. The frozen analysis source was not modified and the raw data were not regenerated.

- Natural analysis JSON: `private/final125_prior_execution_2026-09-08/reports_final_2026-09-08/natural_analysis.json`
- Mixed analysis JSON: `private/final125_prior_execution_2026-09-08/reports_final_2026-09-08/mixed_analysis.json`
- Integrity and independent-check receipt: `private/final125_prior_execution_2026-09-08/reports_final_2026-09-08/integrity_audit.json`
- Raw-data and output hash manifest: `private/final125_prior_execution_2026-09-08/reports_final_2026-09-08/report_manifest.json`
- Analysis folder guide: `private/final125_prior_execution_2026-09-08/reports_final_2026-09-08/README.md`
- Separate post-run integrity check code: `tools/final125_postrun_audit_v1.py`

The folder contains O/X/score/cost CSVs with 125 rows each for natural and mixed, per-role costs, batch Curator, 500 rows of per-body metrics, latency by role and task, and quality and text descriptive statistics. Only the pre-specified computations were performed this time. Additional paid model calls 0, modifications of original texts or scores 0. The unconfirmed usage of the natural H2 was not resolved, and the current analysis is complete with this limitation stated explicitly. It does not mean completion of manuscript integration, full Cloud reconciliation, invoice reconciliation or public release.
