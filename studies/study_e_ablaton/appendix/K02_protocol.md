> English translation prepared 2026-09-17 of `PROTOCOL.md`. The Korean original is the recorded/frozen document; where wording differs, the original governs.

# STUDY-E-ABLATON — Incremental Contribution of Critic Repair Instructions

Status: plan subject to freezing before execution. This is a separate study and does not change STUDY-E-1's H1–H3, raw scores, or analysis rules.

## Research Question and Scope

Given the same mixed initial drafts, company evidence, Planner plans, Researcher ledgers, selected lessons, and Gate information, we compare the incremental effect of the Critic's repair instructions on the final total score. The target is the Critic's incremental contribution within a revision system that already includes Gate information. This is not an experiment that validates the full multi-agent architecture, batch memory, or the population effects of naturally occurring errors.

This is a follow-up study designed after observing the results of the existing STUDY-E-1. The 125 already-known mixed inputs are reused as a fixed benchmark. No claim is made of independent external validation on new, unobserved topics. Inputs, prompts, analysis, order, and failure rules are fixed before any new comparison results are seen. The local plan and hashes are not represented as an AsPredicted registration.

## Inputs and the Two Comparison Groups

All 125 existing mixed original inputs (52 fixed transformations and 73 unchanged) are used. Recovered articles or initially low-quality articles are not singled out. What is copied is the title/body, the writing contract for the topic, the original Planner and Researcher outputs, and the selected lessons. The existing final versions, independent-evaluation scores, final Gate, and success status are excluded from the new model inputs.

- `critic_on`: initial Gate → Critic → Optimizer → Gate → if defects remain, Critic → Optimizer → Gate.
- `critic_off`: the same initial Gate → Optimizer → Gate → if defects remain, Optimizer → Gate.

For every task and replicate, the initial Gate is newly called once, and that exact response is supplied identically to both groups. The first revision is mandatory in both groups, with a maximum of two. Because the post-revision Gate evaluates each group's different text, the outputs need not be identical. The Gate model, prompt, and termination rules are the same. Each group runs in a separate state, and no output becomes an input or lesson for the other group. There are no new Planner/Researcher/Writer/Curator calls.

The two Optimizer inputs use the same field structure. `gate_assessment` is provided to both groups, and only the presence or absence of `critic_repairs` differs. The ablation group receives an empty array. No sham assessments such as "the Critic found no problems" or "preserve as already appropriate" are inserted. In `critic_on`, an empty instruction array is also treated with the same meaning. Plan, evidence, lessons, and length rules are identical on both sides.

**The baseline group is not an exact re-execution of the existing STUDY-E-1.** The existing Optimizer received Critic instructions but did not directly receive the Gate's defect list as a separate field. This study newly runs a controlled comparison in which Gate information is provided directly to both sides. The two results are not pooled with the existing final results.

## Replicates, Randomization, and Sample Size

Three replicates per task are fixed, giving 125×3×2=750 final revision results. These are replicates of each of 125 topics, not 750 independent topics. Replication is an operational choice to examine generation variability and not a guarantee of 80% power. The number of replicates is not increased or decreased according to results. Four pairs are run concurrently in a fixed order, and within a pair the designated group order is followed. The next four pairs start after the four pairs complete. Evaluation runs four at a time in a separate fixed random order.

Random seed 2026090801 shuffles the execution order of task-replicate pairs, and the group to run first within each pair is randomized. The two groups of an individual pair are run at close times. The evaluation order is randomized independently of the generation order. Whether the API supports seeds and the actual request settings are recorded; no claim is made that the same seed guarantees the same result.

The planned minimum difference of interest is 0.5 total-score points (on the 4–20 scale; a practical criterion chosen by the researcher, not a universal criterion from the existing literature). Across 125 tasks, when the SD of the per-task replicate-mean difference is 1/2/3 respectively, the N required for two-sided .05 and 80% power under the normal approximation is about 32/126/283. Therefore no claim is made that N=125 is always sufficient. This calculation is neither the power of the exact randomization test nor an estimate of the actual effect. Favorable cases are not selected on the basis of existing results.

## Evaluation and Analysis

Final versions are evaluated separately with the same Gemini3.8 Flash evaluation model, rubric, and generation settings. The evaluation input contains only the content, approval evidence, persona, and an independent random identifier, and does not contain the condition, Critic output, Gate, replicate number, pair ID, or existing scores. The possibility of incomplete blinding due to differences visible in the title and body remains. Evaluation results are not fed back into production. Existing final scores are not reused.

The primary outcome is the `critic_on − critic_off` difference in the final total score, averaged over 3 replicates within each task, and the mean difference across all 125 tasks is reported. A positive difference favors the Critic group. The new primary comparison compares the two groups directly and does not compare their respective before–after p-values.

The primary test is a two-sided paired randomization test that jointly sign-flips the per-task replicate-difference vector (100,000 iterations, seed 2026090802, Monte Carlo p=(number of extreme values+1)/(number of iterations+1), α=.05). It addresses the null hypothesis of no treatment effect on the fixed inputs, under the premises of randomized group execution order and non-interference between groups. It is a conditional result on inputs that already reflect lessons and not a generalization to the natural topic population. The difference distribution and per-task results are also disclosed. The practical importance and statistical significance of effects below 0.5 points are distinguished. A non-significant result is not used as proof of equivalence or no effect.

Uncertainty is presented alongside as a 95% t reference interval for the per-task replicate-mean difference, with the stated limitation that it does not reflect between-task dependence from shared inputs and sources or the distributional assumption. The analysis code must be frozen after final analysis implementation and synthetic-data checking.

Secondary outcomes are the final low-quality proportion, descriptive statistics of improvement and deterioration relative to the existing initial verdicts, production completion, per-task usage-based cost and latency, and number of revisions. No separate significance tests are attached to secondary outcomes. Previous initial verdicts are preserved separately only as a source of descriptive statistics and are not mixed with the new independent evaluation. Evaluation cost and the initial shared Gate cost are each recorded as separate items. The shared Gate cost is apportioned half to each group for group comparison, and the physical actual call is counted only once.

## Failure, Cost, and Operational Separation

New IDs use the `SEA-` prefix, and study_id is exactly `STUDY-E-ABLATON`. New local ledgers, results folders, and trace tags are used. STUDY-E-1 paths are treated as read-only. New external tracing separates the study ID and environment and does not modify existing traces.

All requests, responses, usage, times, models, input hashes, failures, retries, and output lengths are recorded. A valid low score is not grounds for a retry. The 150–2000-character hard range, the 1200–1500-character target, and title separation are maintained. The maximum of 2 semantic revisions is distinguished from technical retries. Technical retries are at most 3 attempts per call, and cost is not treated as 0 when incomplete or usage is unknown. Groups, order, and replicates are not swapped or substituted with successful tasks.

If either group is technically incomplete, the pair is not silently removed; a completion/missing ledger of the planned 750 results is presented. If the scheduled replicates and evaluations are not secured for all 125 tasks, the primary test for the full cohort is left undetermined and only descriptive statistics of available results are reported. After an operational interruption, execution resumes with the same inputs and the same scientific settings, and successful calls are not charged again.

The new cumulative API cost cap is USD60. STUDY-E-1's remaining limit is not treated as the new study's budget. The next call is not started if the sum of known usage-based cost and the conservative reserve for in-progress or cost-unknown calls exceeds the cap. The reserve is not a billing-guaranteed cap from the provider, and invoice reconciliation is separate. Communication failures with unclear response or usage retain the reserve and halt. Paid execution proceeds after confirming model availability and rates on the execution day, key and external tracing connections, transport, usage, and resume safety, input immutability, and the blinding of actual evaluation requests. SDK automatic retries are disabled, and only valid-response validation failures are left in the ledger, followed by at most 3 attempts.
