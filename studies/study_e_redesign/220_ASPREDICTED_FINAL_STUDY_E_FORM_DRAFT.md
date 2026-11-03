# Study E — AsPredicted form draft

Prepared 2026-09-07 from protocol 215, decision 219, and final125_v1 configuration. This is an input draft, not an AsPredicted submission or a freeze receipt. New experiment attempts: 0 when checked. Local final freeze and external registration remain pending. No new model evaluations or analyses are introduced here.

Trial/self-destruct checkbox: leave unchecked. Keep the author's verified existing details. Study type: Experiment. Data source: Other — LLM-generated English marketing texts via model APIs. Prior registrations with no reused observations: Independent; do not delete historical registrations using Draft. This registration covers both new conditions together.

Preparation note updated 2026-09-07: the prospective sample-size sensitivity review is complete; see private/sample_size_review_v1/README.md. It supports only the limited operational interpretation described below, not a guarantee of adequate power for all criteria. N, allocation, budget, and final-analysis code are unchanged. Local freeze and external registration completion remain to be verified.

## 1) Data collection

No, no data have been collected for this study yet.

## 2) Hypothesis

This study evaluates a role-based LLM marketing-content pipeline under two linked conditions: natural generation and controlled-defect refinement. Within each condition, I assess three prespecified operational criteria: H1, technical production completion for at least 90% of the 125 planned tasks; H2, a coefficient of variation of task-level production cost below 0.25; and H3, at least a 30% relative reduction in low-quality texts from initial to final output. These are observed performance criteria, not significance tests of the thresholds. The study does not identify the causal effect of role separation or compare independent samples of 125 versus 125.

## 3) Dependent variables

H1 is the number of technically completed production tasks with a valid final body of 150–2000 Unicode characters, including spaces/newlines but excluding the title, divided by 125. The target body length is 1200–1500 characters; target deviations are recorded separately from invalid responses. Production completion and evaluation completion are distinct.

H2 is sample SD divided by mean task-level production cost in USD. Costs use provider-reported token usage and the price schedule verified on 2026-09-07, including cache and billed reasoning tokens. Natural-condition production costs include Planner, Researcher, Writer, Gate, Critic, Optimizer, related failed/retried calls, and each batch's Curator cost allocated equally to its planned tasks. Mixed-condition costs include only its new Gate/Critic/Optimizer path and related attempts. Independent evaluation costs are reported separately.

H3 is (B−F)/B, where B and F count initially and finally low-quality texts. A separate Gemini 3.8 Flash evaluator scores persona fit, clarity, actionability, and factual grounding from 1 to 5; any dimension below 3 defines low quality. Total score is 4–20. Initial and final texts are evaluated independently and blindly outside production. The evaluator has no access to stage, condition or defect labels, Gate results, or the counterpart text or score. Task IDs retain the initial–final pairing for the prespecified paired analysis; evaluator outputs do not feed back into refinement or lessons. Identical initial and final title and body within a condition reuse that condition's initial evaluation, with reuse recorded. Role-level attempt latency and body-only Flesch reading ease, Flesch–Kincaid grade, word count, and type-token ratio are also recorded.

## 4) Conditions

There are no human participants. Natural generation uses 125 previously unused topics with a fixed persona, company evidence, briefs, prompts, and rubric. The sequence is Planner→Researcher→Writer→Gate→Critic→Optimizer→Gate. Every task receives one refinement, even if the initial Gate passes; a second Critic/Optimizer/Gate cycle occurs only if defects remain, with at most two refinements. Natural batches contain 31/31/31/32 tasks, start with an empty lesson register, and receive one Curator call after each batch; updated lessons are available to subsequent batches.

The mixed condition reuses these same 125 original Writer drafts, not their refined final outputs. Before any new generation or scores are observed, 52 task IDs are randomly selected and allocated to four fixed transformations, 13 each: unsupported factual claims, enterprise rather than small-business audience, removal of concrete action steps, and disrupted sentence/word coherence. The other 73 drafts remain unchanged and are not assumed defect-free. Seed 20260907 controls the recorded selection, allocation, order, and transformation procedure. Transformations use fixed code, without score-driven editing. The mixed condition runs the same Gate/refinement rules using each source task's saved plan, evidence ledger, and selected lessons; it makes no new Planner/Researcher/Writer/Curator calls. Conditions share source tasks and are analyzed separately.

## 5) Analyses

For each condition separately, calculate H1 completion/125, H2 cost CV, and H3 relative reduction, and compare them with the prespecified criteria. Report initial/final low-quality counts and the four low-quality/pass transitions. Describe the four quality dimensions and total scores at initial and final stages and their paired changes. Report observed/missing counts, mean, sample SD, median, 95th percentile, minimum, and maximum for scores, costs, latency, and text metrics as applicable. Role costs and batch Curator costs are also reported. Latency distinguishes individual attempts, summed direct production-call time per task, and elapsed time from first production attempt to production completion where timestamps exist; evaluation and batch Curator calls are separate from direct task time.

Conduct one two-sided paired Wilcoxon signed-rank test of initial versus final total score per condition, alpha=.05, using Pratt zero handling, average ranks, asymptotic inference, and no continuity correction (SciPy 1.17.1). If all differences are zero, report statistic=0 and p=1. This test does not test H3's 30% threshold. Shared evolving memory and task dependence limit inferential interpretation. No separate dimension-wise tests, between-condition causal tests, defect-type tests, Gate-subgroup analyses, bootstrap intervals, or additional threshold tests are planned. English body-only text metrics use the fixed analysis code's tokenization, punctuation-based sentence counts, and heuristic syllable counts; TTR is case-insensitive unique words/words.

## 6) Outliers and exclusions

No quality-, cost-, or latency-based outlier removal, trimming, winsorization, or task replacement will occur. Retain all 125 planned tasks per condition, including unstarted, incomplete, failed, and missing-evaluation cases. Technical failures (e.g., transport, truncated JSON, schema/ID or hard-length violations) may be retried under fixed limits, preserving every attempt and known cost. Valid low scores are not retry grounds. Missing evaluations are not passes; unknown costs are not zero and are kept separate from budget reservations. If production is incomplete or production usage is unknown, overall H2 is undetermined. If any initial/final evaluation pair is missing, overall H3 and Wilcoxon are undetermined; available-pair descriptions and missing counts remain reported. If B=0, H3 is undefined. Historical pilots and synthetic telemetry checks are excluded from the new experiment data and retained separately.

## 7) Sample size

Following a prospective sample-size review, I retained the planned 125 source tasks for a bounded operational evaluation of the specified pipeline. The historical origin of this task count was a scenario-specific power calculation for a supplementary exact McNemar test. The current-design review examined score-change sensitivity, initial low-quality event availability, and task dependence; it did not establish adequate power for all study outcomes. Results will be interpreted within the evaluated pipeline and conditions. The rationale, calculations, and limitations are archived in private/final_design_sample_size_review_v2/README.md and private/sample_size_review_v1/HISTORICAL_RATIONALE_CORRECTION.md. The author confirmed retention of N=125 on 2026-09-07 before new final data collection.

The planned sample is exactly 125 new source tasks, each contributing a natural and a mixed-condition task record: 125 records per condition, not 250 independent source observations. The mixed condition contains exactly 52 assigned transformations (13 per type) and 73 unchanged drafts. No additional tasks are added based on results. Both conditions share a cumulative budget-ledger cap of USD49.99 and a maximum of 5000 model API attempts, including evaluation and retries. These limits do not reset on resumption. Stop if the next request cannot fit the budget/call limit; retain the planned denominators and report unfinished tasks. The cap is not an estimate of total spending.

## 8) Other

The author has inspected prior Studies A–D and separate Study E model-selection, integration, length, and defect pilots; they informed this design and model choice. None of those generated observations or scores will enter this new experiment. Topic inputs and offline/synthetic implementation checks already exist, but no new experimental model outputs or outcome scores have been collected.

Fixed model IDs are claude-haiku-4-5-20251001 (Planner), claude-opus-5 (Researcher), gpt-5.4-mini (Writer/Critic/Optimizer), gpt-5.4 (Gate/Curator), and gemini-3.8-flash (independent evaluator). Protocol, prompts, settings, topic/order/defect assignments, transformation and analysis code, and pricing will be archived with hashes before new data collection. Mixed input texts will additionally be generated and hashed from the original natural drafts before any mixed-condition model calls. No silent model substitution is allowed.

Per resumption, retry controls are schema 12, transport 7, and rate-limit 24; cumulative budget/call limits remain binding. Equivalent operational runner/telemetry fixes may be documented and resumed with before/after hashes and checks, preserving successful calls. Scientific changes are reported as deviations rather than operational repairs. Langfuse supplies evidence of execution, failures, and refinement cases; final statistics use the complete local task/attempt ledger and fixed analysis code. The evaluator's judgments do not establish human-rated quality, factual truth, or causal benefits of roles or lessons. No additional ablation or human-rating experiment is included in this registration.

## 9) Name

Study E — Role-Based LLM Marketing Pipeline: Natural Generation and Controlled-Defect Refinement

## 10) Type of study

Experiment

## 11) Data source

Other: LLM-generated English marketing texts via model APIs
