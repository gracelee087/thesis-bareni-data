> Appendix copy of `../215_FINAL_EXPERIMENT_PROTOCOL_DRAFT_EN.md` (2026-10-16). Only the Korean topic-bank file name is replaced by an English description.

> English translation prepared 2026-09-17 of `215_FINAL_EXPERIMENT_PROTOCOL_DRAFT.md`. The Korean original is the recorded/frozen document; where wording differs, the original governs.

> The "draft" wording below is kept because the Korean original is hash-locked in `freeze.json` and was not edited after freezing. This is the protocol registered as AsPredicted #310130.

> Note added to this appendix copy on 2026-11-23: there is no GitHub release, Zenodo record or DOI; the materials are provided in this repository.

# Study E Final Experiment — Pre-Registration Protocol Draft

Written 2026-09-06. **This is not yet a document submitted to AsPredicted or finally frozen.** The final conditions were to be registered the following day, after which the 125 new naturally occurring tasks and the 125 defect-mixed tasks that use the same initial drafts were to be run. Today only code/document preparation and offline checks are performed. The existing Study D registration and the Study E pilot raw data are not modified.

## 1. Purpose and What Is Inherited from Prior Studies

This study evaluates the technical completion, the execution-cost distribution, and the change in AI rubric judgments before and after revision of a marketing-content pipeline with fixed case evidence, persona, and business constraints. It does not test actual corporate operation across all five departments, reduction of human labour, marketing revenue, or the independent causal effect of role separation.

This is a follow-up plan prepared after having already seen the results of Studies A–D and the Study E model-selection, connection, long-form, and defect pilots. Failures and unfavourable results are also kept in the development history. Existing pilots are not retroactively treated as new pre-registered data. The scope of authoring, referencing, and author review of the model-selection materials is preserved in [No. 213](L07_model_selection_history.md).

The two runs are reported as the natural condition and the controlled-defect condition respectively. Because the two runs share the same 125 original tasks, they are not 250 independent samples. The full pipeline of the natural run and the revision path of the mixed run differ in role and cost scope.

## 2. Sample and Input Materials

### Experiment 1: 125 new naturally occurring tasks

- Select 125 topics from the author-written topic bank file that have not previously been used or reserved. Topic text normalized for whitespace and Unicode is checked against the historical task banks, execution plans, and used/reserved ledgers. An existing topic given only a new ID is not counted as unused.
- The actual number of selection candidates, exclusion reasons, the past comparison files and hashes used, and each new topic ID, original text, and source location are recorded in a pre-execution selection ledger. If a sufficient number of unused topics is not confirmed, readiness is left incomplete before the first paid call. Unusedness that has not been verified is not claimed.
- The confirmed values of the current preparation ledger are 1899 normalized unique topics, 670 excluded as already used/reserved, and 1229 candidates. Of these, 125 were selected. The [comparison ledger](../private/final125_v1/topic_inventory.json) preserves exact topic matches under NFKC, casefold, and whitespace normalization together with the list of comparison files. This check does not also guarantee the semantic independence of the topics. The [selection ledger](../private/final125_v1/selected_topics.json) and the file hashes immediately before registration are the reference.
- The draft value of the random seed for selection, ordering, and defect transformation is **20260907**. It is frozen by checking the ledger against the actual configuration values in the code immediately before registration. No re-draw is performed to pick topics or defects that would yield favourable scores.
- The persona, company evidence, CF/PF format instructions, rubric, and per-role system/user prompts are preserved as snapshots with hashes. The topic bank is a content direction; the topic wording alone does not establish facts about the company's customers, implementation, or track record.
- The body target is **1200–1500 characters**, and the valid range is **150–2000 characters**. The title is separate and is counted by Python Unicode string length. Hard-range violations and departures from the target range are distinguished and both are reported.
- Batches are 31/31/31/32 tasks. The natural run starts with an empty lesson ledger and updates lessons between batches. The lessons actually selected per task, the plan, evidence, and draft are preserved. This is one sequential memory history, not 125 independent repeated corporate operations.

### Experiment 2: 52 defect tasks ＋ 73 unchanged tasks from the same initial drafts

- Uses the 125 **pre-revision Writer initial drafts** from Experiment 1. The final revised texts of Experiment 1 are not used as the initial texts of Experiment 2.
- Before viewing any outputs or scores, 52 of the 125 scheduled IDs are selected at random and assigned 13 each to four types by the same pre-fixed RNG procedure. The selected IDs and the assignment table are saved before the first natural paid call.
- Each task's Planner and Researcher outputs, company evidence, persona, and the lessons selected for that task are reused as is. There are no new Planner, Researcher, Writer, or Curator calls and no new cross-batch lesson accumulation.
- The remaining 73 use the title and body of the initial draft as is. It is not assumed that all of these texts are sound.
- The new injected texts are produced with the [defect transformation code](../tools/final125_v1/defects.py), which is frozen in advance. There is no free per-text editing by the AI tool and no rewriting until scores drop.
- The four types are **unsupported factual claim, change to a large-enterprise readership, removal of concrete action steps, and corruption of sentence linkage/word order**. 13 per type, one target type per task. Variants per type are 0–12. Titles are kept.
- `fabricated_evidence`: after the original text, insert a sentence stating that Bareni has already deployed to `27+3×variant` paying customers and reduced weekly administrative work by `43+2×variant`%. These numbers are fictitious claims produced by a fixed formula and are not actual performance data. The end of the original may be truncated at a predetermined length so as to stay within 2000 characters.
- `wrong_audience`: prepend a fixed introductory passage designating the board and transformation organization of a multinational with `5000+500×variant` employees as the readers, and replace specific small-business reader expressions with enterprise transformation director. The end of the original is truncated to fit the remaining length.
- `no_actionable_step`: replace the entire body of the original with five abstract reflective paragraphs reflecting only the topic. Paragraph order is fixed by `Random(20260907+variant)`. This is a strong control manipulation that broadly removes actionable content, not a subtle single-sentence omission.
- `incoherent`: shuffle all whitespace-delimited words of the body with `Random(20260907+variant)` and join them with spaces. If the result is unchanged or too short, a code-fixed ungrammatical string repeated 24 times is used, and if even that equals the original, a fixed replacement string is used. This exception is likewise a pre-specified rule that does not look at scores. This is severe synthetic ungrammaticality and is not claimed to be a representative sample of natural errors.
- If, even after applying these fixed exceptions, the body falls outside 150–2000 characters or equals the original, execution halts as a mechanical contract error. No other task is drawn and no wording is changed while looking at quality. Only equivalent input-assembly error fixes that do not change the scientific input are allowed, with history, and if that is not possible the case remains a preparation/execution failure or missing. One manipulation may simultaneously affect multiple rubric dimensions or length, and the target of 1200–1500 characters is not used as an injection-success filter.
- Because the actual originals arise after the natural run, **the transformation rules and selection table are frozen before pre-registration**, and **the 52 original/transformed texts, diffs, and hashes are frozen after natural generation and before the first mixed call**. These two freeze points are not confused.
- Even if a defect was injected, a text that is not low quality under independent evaluation is left as is. Injected texts are not automatically counted as low quality or replaced with other texts. Cases in which the transformation cannot formally be applied are also recorded per the pre-specified exception rule and are not silently replaced.

## 3. Roles and Execution Path

| Role | Selected model | Natural 125 | Mixed 125 |
|---|---|---|---|
| Planner | Claude Haiku4.5 | New run | Reuse the corresponding original result |
| Researcher | Claude Opus5 | New run | Reuse the corresponding original result |
| Writer | GPT-5.4 Mini | New generation of initial draft | Original draft or frozen defect text as input |
| Gate | GPT-5.4 | New run | New run |
| Critic | GPT-5.4 Mini | New run | New run |
| Optimizer | GPT-5.4 Mini | New run | New run |
| Lesson Curator | GPT-5.4 | New run between batches | No new calls |
| Independent outcome evaluation | Gemini3.8 Flash | Initial and final evaluation | Initial and final evaluation |

The table above gives human-readable model names. The actual provider/model IDs, generation settings, output-token caps, unit prices, and API paths are matched to the execution manifest before registration. No other model is silently substituted on grounds of an outage.

The production path of the natural run is `Planner → Researcher → Writer → Gate → Critic → Optimizer → Gate → second Critic·Optimizer·Gate if needed`. Because the Researcher receives the Planner plan and the selected lessons, the two roles are sequentially connected. The mixed run follows the same additional-revision rules after `Gate → Critic → Optimizer → Gate`, starting from the stored upstream materials and the initial text.

The fixed inputs the Writer consults are the five bundles of **persona, approved company evidence, task brief, required/prohibited/preserved constraints, and the lessons selected for that task**. In addition, the actual Planner plan and the Researcher's evidence/usage-condition ledger are passed. An empty lesson ledger or 0 selected lessons is also a valid input, and lessons are not promoted to factual evidence. This connection is preserved via the actually transmitted strings, per-role outputs, and parent-response hashes.

- **The first semantic revision is mandatory for every task**, up to two at most. Even if the first Gate passed the text, the first Critic·Optimizer path is invoked. If defects remain at the Gate after revision, the second path is run, and thereafter no additional quality regeneration is done to remove remaining defects. A generation response that falls outside the hard body-length contract is technically retried as a mechanical contract error for that call and is not counted as a separate semantic revision round.
- The Critic produces revision instructions for the targeted and length issues raised by the Gate. It is not assumed that the Critic independently detects all errors. Text changed by the Optimizer even under empty Critic instructions has the fact and effect of the change recorded as is.
- Prepare a configuration that executes role connection and resumption via actual LangGraph state, nodes, and edges and leaves actual execution traces in Langfuse. Matching only file names or replaying past execution logs as if they were new calls is not done. Runtime and library versions, code hashes, actual trace identifiers, and raw API ledgers are linked.
- Role invocation O/X, non-empty remarks, actual string changes, number of revisions, and evaluation pass are separate variables. O does not mean semantic success or quality improvement.

## 4. Independent Outcome Evaluation and Measurement Limits

The initial value is the initial text produced by the Writer or the frozen input text of the mixed condition. The post-revision text is not substituted as the initial value. Initial and final texts are each evaluated pointwise outside the production path, and evaluation results are prevented from being passed into revision or lesson generation. The actual time the evaluation call is performed and the time the evaluated text was generated are recorded separately.

The evaluator is not given original/injected status, defect type, initial/final status, revision count, Gate verdict, prior scores, pair IDs, or diffs. Task evidence, persona, and rubric are provided. Because severe textual defects are themselves visible, perfect cognitive blinding is not claimed.

If, within the same run, title and body are exactly identical, the initial evaluation is reused as the final value and marked as such. Scores from a different past run are not reused as if they were new evaluations. Cache reuse is not evidence of the evaluator's repeat agreement.

Evaluation is PF/CL/AC/FG at 1–5 points each, and **a text is low quality if any one is below 3**. A critical violation is recorded as 1 point on the relevant dimension. Contradictions between the critical flag and the scores, and schema failures, are not accepted as valid measurements and are left in the technical-error history.

In the selection test, Gemini agreed with the author's standard on 25/30 and missed 5 of 10 subtle defects. Therefore H3 is a change in fixed AI rubric judgments, not a validation of all human quality judgments. Whether an additional author review of the final long-form texts is conducted is decided in a separate plan, and non-performance is not written up as performed.

## 5. Technical Recovery, Halts, and Budget

- The **draft** of the combined budget cap of the two new runs is **USD49.99**. Previous development/pilot costs are not merged with the new experiment cost and existing ledgers are not changed. The actually approved cap, unit prices, and pre-call reservation rules are checked against the configuration files before registration. There are no new paid calls today.
- Technical failures include provider errors, timeouts, JSON truncation, schema/ID contract errors, and tracing/checkpoint problems. The original request, response, error, cost, and time are preserved, and retry/resume follows the frozen recovery rules. A technical retry within one semantic revision is distinguished from a new semantic revision round.
- The technical-attempt caps per resume activation are schema 12, transport 7, and rate-limit 24, and the overall call cap of 5000 for the two runs summed over all resumes and the combined budget of USD49.99 are not reset. Budget and overall call caps are not circumvented by increasing the number of resumes. These values are also checked against the manifest immediately before registration.
- To allow recovery through to the end, equivalent technical bugs in the execution/tracing code may be fixed at the cause and resumed. The permitted recovery sources are the runner and telemetry; the reason for the change, files, before/after hashes, affected attempts, and resume point are recorded, and successful valid calls are reused. Changes to models, rubric, score thresholds, defect selection, input semantics, the maximum number of semantic revisions, and other scientific sources are not included in this equivalent-recovery allowance. If such a change is required, the existing run is preserved and it is handled as a new protocol/deviation from registration.
- No retry is performed because a score is low or a hypothesis criterion was not met. A normal low-score response is not converted into an error. If a semantic rule change affecting results is required, the state of the existing run is preserved and it is reported as a deviation from registration.
- Budget, balance, and rate limits are checked before each call. Balance exhaustion halts separately from rate limiting. If technical completion within budget is not achieved, it remains incomplete. Tasks are not deleted or replaced by successful tasks to produce 125/125.
- Langfuse transmission failures are recovered by preserving raw records and the pending-upload state. Trace completeness and task production completion are reported separately; trace gaps are not hidden and valid model calls are not needlessly repeated.
- Production completion, evaluation completion, and study completion of all 125 tasks are managed as separate states. Missing evaluation does not erase the existence of the product, but neither does it make the whole of H3 evaluable.

## 6. H1–H3 Definitions and Verdicts

| Item | Natural 125 | Mixed 125 | Point criterion |
|---|---|---|---|
| H1 | Tasks whose production path is technically complete and which have a final body of 150–2000 characters / scheduled 125 | Tasks whose revision path starting from stored upstream satisfies the same completion condition / scheduled 125 | Observed completion rate≥.90 |
| H2 | Generation·Gate·Critic·Optimizer·related failures/retries and equal allocation of the corresponding batch Curator cost | Only this run's new Gate·Critic·Optimizer·related failures/retries | Sample SD/mean of per-task production cost<.25 |
| H3 | Relative reduction in low quality between initial draft and final text | Relative reduction in low quality between the defect 52＋unchanged 73 inputs and the final texts | Observed relative reduction≥.30 |

H1 is technical completion under the recovery policy, not content accuracy or the independent-evaluation pass rate. H2 is the variation in production cost across tasks within the given execution window, not predictive power for future cost or cheapness of cost. H3 is not a 30% rise in overall rubric scores or the causal superiority of role separation. Meeting a point criterion is not used as equivalent to statistical confirmation or generalization.

### H2 cost verification and unverified usage

Evaluator cost is separated as measurement cost and excluded from H2. Known token usage is converted at pre-fixed unit prices, and known usage from failures and retries is also included. This is distinguished from amounts reconciled against the actual invoice.

The 2026-09-07 officially verified unit prices use `private/final125_v1/pricing.json` as the single ledger. The same file and hash are applied to reservation, observed cost, and Langfuse transmission in the final run. Cache and thinking are not double-counted, and the GPT-5.4 long-context tier and Anthropic cache-retention-period unit prices are applied. OpenAI is requested with the standard service tier, and expiry of price validity, mismatch between plan and unit prices, and inability to verify cost are grounds for halting calls. Verified itemized costs are sent directly to Cloud. Technical errors are preserved as ERROR with error metadata, and content defects as Gate results. Cloud transmission failures are kept locally and the model is not called in duplicate. Synthetic traces for price verification are separated into the `pricing-verification` environment and excluded from the experimental analysis.

Calls whose usage cannot be verified are not changed to a cost of 0. The known-usage cost, the reserved amount for unverified calls, and the overall budget ledger are each reported. If unverified production usage remains or production is incomplete, H2 on the basis of all completed tasks is **undetermined**. A separate known-cost-only CV or reservation-book CV is not added as a final analysis. Per-task known cost and reserved amount are disclosed as separate ledgers, and reserved amounts are not substituted for actual cost.

### H3 event counts, missingness, and unit of analysis

Let B be the initial low-quality count and F the final low-quality count; then `R=(B−F)/B`. Both initial low-quality→pass recoveries and initial pass→low-quality deteriorations are reflected. The initial and final low-quality counts and the counts of the four transitions are disclosed as descriptive records that explain the arithmetic of B−F. Initial and final per-dimension scores and total-score changes are also reported as descriptive statistics. No separate per-type hypothesis tests or Gate-subset numeric tables are added.

- If B=0, relative reduction is undefined. Initial quality and final deterioration are reported as they are.
- Even if B is 1–9, the observed values, the event counts, and the interpretive limits of few events are disclosed. The past operational lower bound of 10 is not used as a scientific minimum sample size. 100% recovery of few events is not interpreted as certain general performance.
- The sample of 125 and the 52 injections are fixed sizes chosen considering resources, coverage, and type balance. No guarantee that the 52 will necessarily be low quality, and no claim of 89% overall H3 power, is made.
- All 125 scheduled tasks are kept in the analysis ledger. Tasks with missing initial or final evaluation are not treated as successes. If the full set of pairs is not obtained, the primary H3 point verdict is left undetermined, and descriptive statistics of valid pairs and the missing count are given together. No upper/lower bound calculation assuming missing labels is added. Values analysed on completers only are not presented as the result for all 125.
- Effect sizes for the natural 125 and the mixed 125 are reported separately. Simply subtracting different run/memory conditions is not interpreted as the pure causal effect of defect injection.

### Statistical methods specified in the Proposal

The final numerical analysis is limited to **the calculations specified on Proposal.pdf pp.5–6**. H1≥.90, H2 CV<.25, and H3 relative reduction≥.30 are observed point criteria. Descriptive statistics and the Wilcoxon below are reported, and the significance of the Wilcoxon is not substituted for a test result of the three point criteria themselves.

- For each task's four dimensions PF/CL/AC/FG and the total score (4–20), report the observed count, missing count, mean, sample SD, median, 95th percentile, minimum, and maximum for initial, final, and paired differences. Failed/incomplete tasks are also kept in the ledger; they are included if an evaluation actually exists, and absent values are left missing.
- **A two-sided Wilcoxon signed-rank test of initial vs. final total score, α=.05**, is computed once. It is fixed to Pratt zero handling, average ranks and the asymptotic method, and no continuity correction, and the SciPy version is recorded. If all paired differences are 0, statistic 0 and p=1 are displayed. If all 125 pairs are not obtained, the full-cohort test is undetermined. No additional test is attached to each of the four dimensions.
- This test is reference inference about the signed-rank location difference of initial and final total scores and does not test the 30% relative-reduction boundary of H3. Because of the cross-batch memory dependence of the natural run, the two conditions sharing the same originals, the difference-distribution assumption, and the fixed AI evaluator, it is not overstated as evidence of independent samples or of a causal effect.
- Cost is presented as per-task descriptive statistics within the H2 production scope and known per-role call cost. Evaluation cost is separate measurement cost, and Curator is per-batch cost. Unverified cost is left in the ledger, and the sum of the known portion is not called total actual cost.
- Latency is reported as `latency_ms` descriptive statistics over all API attempts of each role and the per-task sum of production call time. Failures and retries are included, and attempts with unverified latency are not changed to 0ms. The per-task call sum adds only direct production calls and excludes evaluation and batch Curator. Curator latency is reported separately per role.
- Task wall-clock is from the `created_at` of the task's first direct production call to `production_completed_at`, including waiting and resume time within it. It is a different value from the call sum. It is not computed if start/end is absent. The report shows observed latency together with missing counts and does not estimate the total time from partial call sums alone.

### The four body-text statistics

The reference-free metrics on Proposal p.6 are **Flesch reading ease, Flesch-Kincaid grade, word count, lexical diversity**. They are computed on the initial and final **body only**, excluding the title. The following deterministic rules are frozen for English text.

- A word is a `[A-Za-z]+(?:'[A-Za-z]+)?` token. The type-token ratio, case-insensitive unique word count / total word count, is used as lexical diversity.
- Sentences are counted as the number of times a run of the punctuation marks `. ! ?` is followed by whitespace or end of string, and a non-empty body has at least 1 sentence. Syllables are an approximation applying the terminal-e exception (excluding le/ye) to the count of English vowel groups, with a minimum of 1 per word.
- With W=word count, S=sentence count, Y=approximate syllable count, ease=`206.835−1.015(W/S)−84.6(Y/W)` and grade=`.39(W/S)+11.8(Y/W)−15.59`. An absent body is missing, and the readability metrics/diversity of a body with no words are undefined. Values are not truncated or regenerated according to whether they are favourable.
- Descriptive statistics of the four metrics for initial, final, and paired differences are reported with the same observed/missing notation as above. Word count and diversity are affected by length and the token rule, and the readability metrics are English approximation formulas. These metrics are not claimed to validate factual accuracy, persona fit, or overall rubric validity.

## 7. Revision of Analysis Scope and Reporting

In the final revision, the Study D-style intervals, resampling, separate boundary tests, and Gate cross/subset numeric analyses that had been added to the earlier 215 draft were removed from the final protocol. The analysis files, values, and S1/S2 reports of existing pilots are preserved as past records and are not retroactively modified. Earlier drafts or past approvals are not used as the basis for the new final analysis.

Per-task O/X, success/failure and reuse distinction, Gate raw text, scores and lengths, defect original/transformed/revised texts, all attempts with known cost and reservation, batch and lesson history, runtime patches, and trace gaps are preserved as **operational raw data and audit records**. Preservation itself does not mean that a Gate×independent-evaluation table or a separate effect/cost analysis of Gate-passed texts is executed.

The Proposal metrics for the natural 125 and the mixed 125 are reported separately. The two conditions are not merged as 250 independent observations, and the difference between conditions is not interpreted as a pure causal effect. The full set of generated texts is not appended to the PDF body; instead the body summary, appendix detailed procedures, and GitHub/Zenodo versioned raw data are linked.

## 8. Execution State to Confirm Immediately Before Registration

- Agreement of this document with the selection ledger, model/pricing/budget configuration, prompts, defect code, and analysis code.
- Reproduction of the 125 actually unused topics and the selection/ordering/assignment ledgers with seed 20260907.
- Actual LangGraph connection, Langfuse configuration and trace path, and checks of input, length, routing, recovery, cost, and missingness analysis run without the API.
- After the author's final confirmation, link the commit hash and configuration hash to the registration text and record the pre-registration completion time. Do not run the first paid natural call before registration.
- Freeze code, analysis, and exception rules before seeing any new experimental results. Final input texts are generated according to the rules and then preserved with stage-by-stage hashes.

Analysis implementation: [analysis.py](../tools/final125_v1/analysis.py). This document is the reference draft for a run in preparation and does not claim, on the basis of offline checks alone, that actual paid execution, external tracing, or pre-registration has been completed.
