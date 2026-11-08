# Correction: the historical quantitative basis for N=125

Reviewed: 2026-09-07. No new experimental model calls.

## Correction and documentary status

The initial 2026-09-07 audit incorrectly stated that no formal power calculation had determined N=125. The search missed the historical sample-size planning document and its code. That statement is withdrawn. The prospective Study E sensitivity calculations remain unchanged; this correction concerns historical provenance and interpretation.

The [original planning document](../../../../최종실험_표본수결정_v1.0.md), dated 2026-08-07, already contained the calculation in Git commit `715cbf58` (author timestamp 2026-08-07T13:19:40+02:00). Its status explicitly described a pre-confirmatory planning candidate, conditional on task-bank/budget approval and freezing. It must not be described as a completed freeze or approval receipt. The document was subsequently revised in commits `38b7ff38` and `08589f64`; the original version already stated the .10/.90 scenario and minimum N=125.

## Reproduced historical calculation

For independent tasks, D ~ Binomial(N,q) counts discordant initial/final low-quality statuses, and X | D ~ Binomial(D,p) counts improvements among those discordances. The calculation sums the rejection probability of the two-sided exact binomial test of p=.5 at alpha=.05 over D. This is unconditional power for a supplementary exact McNemar test. The binomial form of the exact test is also documented in the [statsmodels reference](https://www.statsmodels.org/stable/generated/statsmodels.stats.contingency_tables.mcnemar.html).

Under q=.10 and p=.90:

| Tasks | Power |
|---:|---:|
| 100 | 66.96% |
| 120 | 77.94% |
| 124 | 79.70% |
| 125 | 80.12% |

An independent SciPy binomial calculation scanned every integer N from 1 through 125 and confirmed that 125 first reaches 80%. The [original implementation](../../../../code/bareni_pipeline/sample_size.py) agrees to numerical precision. The planning assumption was less optimistic than Pilot 8's four improvements among four discordances in 30 tasks; 90% directional improvement remains a strong assumed asymmetry, not a universally conservative effect.

This calculation supplies a quantitative reason for the original choice of 125. It does not guarantee power for H1/H2, directly test the 30% relative-reduction threshold, or justify the changed Study E total-score Wilcoxon test. Retaining a historical sample size and computing a new study's power are separate decisions. The historical document also mentions estimation stability, task diversity, and budget considerations; it does not demonstrate an optimized budget-derived N or equal precision across studies.

## What the later 2,796 / 7,075 calculations mean

[Planning document 193](../../193_H123_SAMPLE_SIZE_PLANNING.md) uses a different test and assumptions: independent identically distributed tasks, one-sided alpha=.05, Z=.7 I-F, and a studentized Wald statistic for the population relative reduction exceeding .30. Initial low-quality probability is assumed to be .016, repair probability .50, and harm probability among initially passing texts either 0 or .001.

| Assumed harm probability | Approximate candidate N | Simulated power at candidate N | Boundary-null rejection at candidate N | Simulated power at 125 |
|---:|---:|---:|---:|---:|
| 0 | 2,796 | 83.188% | 3.722% | 3.792% |
| .001 | 7,075 | 80.911% | 4.597% | 3.293% |

Both candidate sizes and all listed Monte Carlo results were reproduced using the recorded random seeds and 100,000 draws. They are alternative-variance approximations followed by scenario checks, not exact minimum sample sizes. The .016 initial rate came from an earlier pilot context and is not a known population parameter. It differs from the .024 scenario used in the later prospective sensitivity review. Neither rate is automatically applicable to the controlled-defect condition.

Do not write that the study's "actual power is 3–4%" or that it universally "requires 2,800–7,100 tasks." The results apply to this particular stronger test and sparse-event scenario. They neither contradict the historical McNemar result nor describe the current total-score Wilcoxon test. Sparse events also make the large-sample Wald approximation problematic at N=125. The new final analysis continues to treat the 30% reduction as an observed operational criterion; no Wald or McNemar test is added by this correction.

## English wording for the new Study E

> The planned sample comprises 125 new source tasks, retaining the historical task count. The original quantitative basis for this number was a power calculation documented on 7 August 2026 for a supplementary two-sided exact McNemar test. Assuming independent tasks, a discordance probability of .10 and an improvement probability of .90 among discordant pairs, N=125 was the first integer achieving at least 80% power at alpha=.05 (80.12%). This calculation does not establish adequate power for the changed Study E design, its total-score Wilcoxon analysis, or H3's 30% relative-reduction threshold. A separate sensitivity review conducted before final Study E data collection therefore examined initial-event availability, score distributions, and dependence. The 30% threshold is interpreted as a prespecified observed operational criterion, and conclusions are restricted to the evaluated pipeline and conditions.

For the historical manuscript, Section 3.5 now separately describes the original rationale and Study D's later event-availability check. Appendix G.7 reports the later Study E scenarios with their assumptions; Table 3-2 points to Section 3.5. This avoids presenting a later design calculation as the original reason for historical sample selection.

## Verification and preservation

The [reproduction script](../../tools/verify_historical_sample_size.py) uses no model clients or credentials and refuses to overwrite its receipt. The [calculation receipt](historical_calculation_verification.json) records source hashes, versions, exact powers, independent cross-checks, and the reproduced later scenarios. Historical source documents, code, and recorded scenario outputs were unchanged. The earlier `verification_manifest.json` remains an archival snapshot of the earlier review, not a verification of corrected prose. The follow-up `historical_correction_manifest.json` records the corrected documents.
