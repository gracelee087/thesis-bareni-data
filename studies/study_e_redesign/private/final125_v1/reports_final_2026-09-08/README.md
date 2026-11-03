# Study E final reports

These files are derived from immutable local records; this program makes no API calls.
Each cohort retains its 125 planned tasks, including missing or unfinished records.
report_status=not_started or in_progress_or_incomplete is a progress snapshot,
not a final experimental result. Planned-only 0/125 is not an observed final failure.
The two cohorts share 125 source tasks and are not 250 independent observations.

O = at least one NEW API attempt for that stage in this cohort; X = no new attempt.
O does not mean success, correctness, text change, or quality improvement.
The adjacent attempt/success/source columns distinguish these cases. A resumed call
served from a previously successful result is still one original call, not another API attempt.
Mixed Planner/Researcher/Writer are X with artifact reuse; final evaluation is X when
the recorded exact-text reuse rule supplies the initial evaluation.

Lesson Curator operates after a natural batch, not once per task. Repeated batch
columns in task CSVs are context only: count calls from batch_curator_activity.csv.
The mixed cohort makes no new Curator calls and reuses saved per-task lessons.

tasks/{id}.json takes precedence over production/{id}.json. A production checkpoint
can establish technical completion while evaluation is missing; it does not invent
an outcome. Successful evaluation attempts may fill checkpoint measurement fields.
Unresolved started calls are charged their unknown reservation in memory only; no
raw result is written or overwritten. Unknown production usage makes primary H2
undetermined. Reservations remain separate budget records, not observed usage cost.

H3 missing pairs prevent a full-cohort primary point verdict. Valid-pair descriptive
counts and missing counts remain visible. Few initial events are reported without
an invented scientific minimum of ten. H1/H2/H3 are Proposal point criteria.

Numerical analyses follow Proposal.pdf pp.5-6: completion, production cost CV,
low-quality relative reduction, descriptive cost/latency/four quality dimensions,
body-only English Flesch ease/grade, word count and unique-token/word-count lexical
diversity, and the paired four-score-total Wilcoxon test (two-sided alpha=.05,
Pratt zero handling, asymptotic method without continuity correction). Missing
pairs prevent the full-cohort test; unchanged pairs are retained. The Wilcoxon
null is not the H3 30% boundary. Shared evolving memory limits reference inference.
No additional inferential procedures or numeric Gate subset/crosstab are generated.
Raw Gate and O/X audit fields remain available without adding statistical tests.

Text metrics describe English surface form, not factual correctness. See JSON
analysis_settings for frozen formulas and token/syllable rules. CSV contains 500
planned text rows; absent body values remain missing, not deleted. Latency role
rows count all attempted calls, including failed or pending calls. Task call-sum
excludes evaluation and batch Curator and is not wall-clock. Wall-clock uses the
first direct production attempt to production completion, with waits and resumes.
Missing timestamps/latencies are not zero; known partial sums are audit fields.

No report is a substitute for preregistration, source/trace verification, or invoice reconciliation.
