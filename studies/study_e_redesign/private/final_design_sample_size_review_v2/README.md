# Final Study E: sample-size review against the current design

Prepared 2026-09-07, before new final-experiment data collection.

**Review conclusion:** This review does not derive 125 as a necessary or sufficient sample for the current design. Conditional sample-size calculations are possible and have been performed. A single final powered N cannot be selected without a substantively justified target effect or precision and a defensible dependence model. No sample size, allocation, analysis rule, model, budget, or historical record was changed. No model calls were made.

**Subsequent author decision, 2026-09-07:** After being informed of these limitations, the author explicitly chose to retain the existing 125 source tasks and describe the choice transparently as a bounded operational evaluation. Each source contributes one natural and one mixed record, with 52 transformed and 73 unchanged mixed drafts. This resolves whether to retain the task count; it does not turn the review into evidence of adequate power or an optimized N. The two conditions keep their separate analyses and the existing missing-data and budget/call stopping rules. No outcome-dependent sample changes are permitted. This decision does not complete the freeze or external registration.

Authoritative calculations: [verified/results.json](verified/results.json). Reproducible script: [final_design_sample_size_review_v2.py](../../tools/final_design_sample_size_review_v2.py). The top-level `results.json` is a superseded development output: the verified run uses upward rounding for hypothetical completion counts, clips numerical convolution probabilities to [0,1], and records checks immediately below each conditional minimum. It must not be substituted for the verified output.

## What was evaluated

The current design has 125 natural source tasks and a linked mixed condition using the same original Writer drafts, with 52 transformations (13 per type) and 73 unchanged drafts. Natural production has one evolving lesson history across four sequential batches. The final numerical policy is [Decision 219](../../219_PROPOSAL_ONLY_ANALYSIS_DECISION.md).

H1 completion >=90%, H2 sample cost CV <.25, and H3 observed relative low-quality reduction >=30% are operational criteria, not three population-threshold significance tests. The supplementary test is the paired total-score Wilcoxon test, two-sided alpha=.05, Pratt zero handling, asymptotic method, no continuity correction, SciPy 1.17.1. Its estimand is not H3's 30% relative-reduction threshold. Planning calculations below do not add intervals, simulations, or new tests to the final analysis.

N candidates: 75, 100, 125, 150, 200, 250, 500, and 1,000. For the natural score scenarios, every integer N from 1 to 1,000 was additionally scanned. H1 and event availability use binomial calculations. Natural three-point score scenarios use exact distributional integration of the specified asymptotic test's rejection region. Cost, mixed-score, and dependence scenarios use 20,000 simulated datasets each, seed 202609071402. Full-sample Monte Carlo probabilities have maximum standard error 0.354 percentage points; per-estimate errors are in the JSON. Simulated 100% does not establish certainty.

## 1. Conditional Wilcoxon sample sizes under the natural score ceiling

The preserved natural pilot's initial mean was 19.704/20 and 99/125 initial texts were at 20. The scenarios reuse only the INITIAL score distribution, never observed pilot changes or p-values. Independent future tasks are assumed. In each scenario, a text first has a 1% probability of losing one point, subject to the score floor; otherwise a text below 20 gains one point with probability r. Remaining changes are zero. This is a deliberately simple -1/0/+1 model, not an estimated future transition model or an effect-size recommendation.

| Assumed r among eligible, non-damaged texts | Expected mean total-score change | Rejection at N=100 | Rejection at N=125 | First integer N reaching 80% |
|---:|---:|---:|---:|---:|
| .25 | +0.04148 | 39.01% | 47.14% | 254 |
| .50 | +0.09296 | 85.74% | 92.84% | 87 |
| .80 | +0.154736 | 99.12% | 99.84% | 45 |

At N=253/254 the first scenario gives 79.8259%/80.0062%; at N=86/87 the second gives 79.7301%/80.2156%; at N=44/45 the third gives 79.4584%/80.3947%. All smaller integers were checked. Same-activity symmetric-null rejection at these three candidate minima is 4.81%, 4.32%, and 4.45%, respectively. The asymptotic test is discrete and not exactly size .05 throughout the N grid; calibration values are reported separately.

For -1/0/+1 differences, the asymptotic Pratt statistic simplifies to (positive_count-negative_count)/sqrt(nonzero_count). This shortcut was checked against the pinned SciPy settings on 1,000 generated difference arrays, including all-zero and all-positive arrays. Binomial integration then gives rejection probabilities without Monte Carlo uncertainty for the natural iid scenarios. This does not make the underlying Wilcoxon test an exact test, remove model uncertainty, or establish independence in the actual pipeline.

**Interpretation:** Neither 125 nor 254 is a universal answer. Different explicit transition assumptions produce different N. The target improvement probabilities have not been selected on substantive grounds, and no scenario should be chosen because its answer is close to a preferred sample size. The N=45 and N=87 values concern the natural supplementary test only; they are not proposed sizes for the complete linked design with 52 fixed transformations. A nonzero mean alone does not determine Wilcoxon power; the full difference distribution matters.

## 2. Natural H3 remains constrained by event availability

Assume independent initial low-quality statuses with probability .024, using the earlier natural pilot's 3/125 only as an uncertain planning scenario.

| Natural tasks | Expected initially low-quality texts | Probability of at least ten |
|---:|---:|---:|
| 100 | 2.4 | 0.0153% |
| 125 | 3.0 | 0.0917% |
| 250 | 6.0 | 8.14% |
| 500 | 12.0 | 76.08% |

For a 95% probability of at least ten events, the first N is 652; for at least twenty, 1,158. If the assumed initial rate is .05, those numbers are 311 and 554; at .10, 154 and 275. The .024 rate is neither known nor representative by assumption. Ten and twenty are illustrative event-count landmarks, not new eligibility rules or sufficient-power thresholds.

At N=125 and p=.024, P(B=0)=4.80%; H3 is undefined in that event. If B>0 and pairs are complete, current rules still calculate H3. A small B does not automatically make H3 undefined. Increasing N can provide more initial cases, but it does not by itself validate the evaluator or turn an observed 30% reduction into a population-threshold test.

## 3. Increasing N also changes the mixed condition unless allocation is addressed

Two counterfactual scaling options were evaluated without changing the plan: keep 52 transformations, or approximately preserve the 52/125 transformation fraction while retaining equal counts in four types. At N=125 the options coincide. At N=250 they imply 52 versus 104 transformed texts. At N=100 the approximately balanced fraction gives 40 transformed texts, not 52. Thus a new N requires an explicit allocation decision; it is not merely more observations of an otherwise identical mixture.

For transformed initial-low probability .80 and unchanged probability .024, N=125 gives 43.352 expected initial-low texts. At N=250, keeping 52 transformations gives 46.352, while using 104 gives 86.704. The transformation count is not automatically the H3 denominator.

The mixed score simulations preserve the pilot's five INITIAL-score strata (four transformation types and unchanged). Under the one-point model with r=.25 and harm probability .01, the fixed 52/73 design at N=125 has an estimated Wilcoxon rejection probability of 98.84% (Monte Carlo SE .076 percentage points); its same-activity symmetric-null rejection is 5.12%. This is a conditional score-test result, not H3 threshold power, validated real-world repair performance, or a guarantee for the actual shared-source/template process. No lower N is selected from this illustrative result.

## 4. More tasks in four batches do not resolve dependence

For a separate symmetric midscale null model, initial total=12 and differences=clip(round(2Z),-8,8), Z has independent task noise plus a shared Gaussian batch component. Keeping four balanced batches gives:

| N | Independent tasks: zero-shift rejection | Latent within-batch correlation .05: zero-shift rejection |
|---:|---:|---:|
| 100 | 5.00% | 17.71% |
| 125 | 5.27% | 20.39% |
| 250 | 4.92% | 32.28% |
| 500 | 4.91% | 45.81% |

These correlations and error rates were not estimated from the study. The calculation illustrates how treating increasingly large dependent batches as independent tasks can worsen calibration. It is not a prediction that the actual experiment has a 20% false-positive rate. The real evolving lesson history may connect different batches as well. Four batches are not four independently initialized pipeline replications. An iid sample-size calculation cannot alone establish calibrated power for the current sequential design.

## 5. H1, H2, missing data, and resources

H1: 113/125 completions would meet the observed 90% criterion; an illustrative Wilson 95% interval would be 83.97–94.42%. At 119/125, it would be 89.92–97.78%. These planning intervals do not establish a population completion rate above .90 and are not added to final reporting. A desired precision has not been specified.

H2: with independent lognormal costs and population CV=.20, the central 95% sampling range of sample CV is approximately .171–.230 at N=100, .173–.227 at N=125, .181–.219 at N=250, and .187–.213 at N=500. These are hypothetical sampling ranges, not confidence intervals around observed costs. At population CV=.25 and N=125, the observed CV falls below .25 in about 52.68% of simulations; this is criterion attainment, not power for a population-threshold test. The lognormal assumption omits unknown tail behavior and actual memory dependence. No precision target has been adopted for H2.

The final complete-data rules also matter. Under an illustrative independent 1% probability per task of unresolved information relevant to a criterion, the probability all tasks are resolved is .99^N: 28.47% at 125 and 8.11% at 250. This is not an estimated outage or usage-error rate. Increasing N does not fix missing-cost accounting. The combined USD49.99 cap remains a stopping constraint, not a demonstrated budget-derived N or verified cost forecast for larger designs.

## Recommendation and remaining scientific decisions

Do not describe 125 as the minimum obtained from the final Study E design. Do not replace it mechanically with 254, 652, or 1,158: those answer different, assumption-dependent questions. Historical McNemar power remains the original quantitative provenance, not the current design's power calculation.

For the currently authorized bounded operational evaluation, retaining 125 is a disclosed design choice supported by these information/limitation scenarios; it is not a claim of adequate confirmatory power. If a newly power-derived N is required, first specify the primary inferential objective, the smallest meaningful change or desired precision, and how task dependence will be addressed. H1/H2/H3 cannot all inherit the supplementary score test's power. Changing to a formal H3 population-threshold test or independent pipeline replications would be an explicit design/analysis revision before freezing.

The review is complete as a numerical and methodological audit. The author has subsequently decided to retain N=125 for the limited operational scope described above. A newly power-derived minimum remains unestablished because those scientific targets and dependence assumptions are unspecified; that stronger claim is not made. No new experiment was started and no registration or freeze was created.

## Reproduction and provenance

Run the script with `--output-dir` pointing to a new directory; it refuses to overwrite `results.json`. It blocks socket connections, verifies final tested source hashes and no new experiment records, preserves all historical files, checks score-test equivalence, verifies event-count boundaries and sample-size crossings, and compares source hashes before and after calculation. The accompanying verification manifest records the final report and result hashes. The full experimental test suite was not rerun because its tested sources were unchanged.

Methodological context: [Lakens, Sample Size Justification](https://lakens.github.io/statistical_inferences/08-samplesizejustification.html) distinguishes power, precision, resource-based justification, and sensitivity analysis. [SciPy Wilcoxon documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.wilcoxon.html) describes the test and its assumptions; calculations here use the locally pinned 1.17.1 implementation, not the current online version.
