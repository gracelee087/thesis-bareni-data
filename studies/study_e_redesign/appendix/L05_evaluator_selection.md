> English translation of `../21_EVALUATOR_PRICE_MATCHED_V3_RESULTS.md` prepared for the thesis appendix (2026-10-16). The Korean original is unchanged and remains authoritative for wording.

# Study E Price-Matched Candidate Evaluation v3 Results

Run date: 2026-09-05. Status: **90/90 closed; analysis completed after freeze verification**.

## 1. Selection conclusion

In this candidate set, **gemini-3.8-flash** passed the frozen selection rule. It had 30/30 valid evaluations, detected all 10 critical defects defined by the author reference, and had 5 false negatives and 0 false positives. This does not mean it is a perfect evaluator or an evaluator whose external validation has been completed.

Mini and Haiku were excluded because of missed critical defects or the absence of a valid evaluation for the relevant items. It is not the winner of a unit-price comparison but **the candidate that passed the evaluator selection rule on this material, rubric, and output contract**. The earlier v2 Luna selection result is not deleted, nor is it treated as included in this comparison. The evaluator setting of the full pipeline was not changed automatically.

## 2. Execution and verification

- 3 candidates × 30 existing author-reference items = 90 main evaluations. Request attempts also numbered 90, with 0 retries and 0 connection failures.
- The run was executed after a separate synthetic compatibility test passed 6/6. Combined with the main evaluation, this round made 96 generation calls.
- Local tests passed 12/12. Immediately before execution, the SDK and Python versions, account access, and configuration hash checks passed.
- The analyser confirmed that all 90 unique candidate–item pairs exist and that every result references the same frozen manifest. No configuration or response was modified during the evaluation.
- 79 valid evaluations and 11 semantic-consistency validation failures. These were not JSON syntax failures or schema_version errors but rule violations between scores and verdicts. Failed responses are also included in the cost and raw data.
- First request started at 09:11:53 UTC; last request started at 09:19:51 UTC. Candidate responses and the individual start times and latencies are preserved in the raw data.
- Frozen SHA-256: `d0d75c352f440a9832dc4de95cd242d6f8b9253aaff261c0bae743851658ff3f`.

## 3. Evaluation results

| Metric | GPT-5.4 Mini | Haiku 4.5 | Gemini 3.8 Flash |
|---|---:|---:|---:|
| Closed items | 30 | 30 | 30 |
| Valid evaluations | 27 | 22 | 30 |
| Semantic validation failures | 3 | 8 | 0 |
| Request/connection failures | 0 | 0 | 0 |
| Critical defects: valid detections / 10 | 2/10 | 2/10 | 10/10 |
| Critical defects: missed among valid responses | 5 | 1 | 0 |
| Critical defects: unscored due to invalid response | 3 | 7 | 0 |
| FN: author fail judged as pass / valid author fails | 8/17 | 9/13 | 5/20 |
| FP: author pass judged as fail / valid author passes | 0/10 | 0/10 | 0/10 |
| pass/fail agreement / valid evaluations | 19/27 (70.37%) | 13/22 (59.09%) | 25/30 (83.33%) |
| Four-dimension score MAE | 0.6389 | 0.7159 | 0.3500 |
| Median latency, ms | 2,166.5 | 9,347.0 | 4,347.5 |
| Selection eligibility | Excluded | Excluded | Passed, selected |

Invalid responses are dropped from the FN and FP denominators but are not regarded as correct verdicts. All 10 critical defects are accounted for by the sum of detections, misses, and unscored cases. Ranking models only by accuracy over valid responses could hide their differing missing denominators.

Gemini FN items: EVAL-BLIND-005, 006, 016, 020, 024. Because it passed 5 of all 20 author fails, we do not conclude from its success in detecting critical defects alone that it is sufficiently safe for general defect verdicts as well.

First reported error of the semantic validation failures:

- Mini: 2 violations of the rule that the primary dimension of a critical defect must be scored 1, and 1 mismatch between the four-dimension sum and total_score.
- Haiku: 7 violations of the primary-dimension score rule for critical defects, and 1 inconsistency between pass and the score/CV verdict.
- These are the errors first reported by the validator; this does not mean the failed responses have no other problems. No post hoc score correction or re-scoring was performed.

## 4. Actual recorded tokens and cost

The figures below are **totals over 30 main evaluations each** and include invalid responses. They differ from official maximum token capacities or request limits. They are estimated costs obtained by applying the frozen unit prices to provider usage reports, prior to invoice verification.

| Requested model ID | Response model ID / version | Total input | Total billed output | Of output, reasoning/thinking | Estimated cost USD |
|---|---|---:|---:|---:|---:|
| gpt-5.4-mini | gpt-5.4-mini-2026-03-17 | 49,079 | 6,651 | 0 | 0.06673875 |
| claude-haiku-4-5-20251001 | Same | 81,212 | 9,486 | Not separately reported (normalised value 0) | 0.12864200 |
| gemini-3.8-flash | Same | 40,031 | 32,145 | 23,736 | 0.15056700 |

Cache read and write tokens were 0 for all three candidates. Google's output of 32,145 is candidates 8,409 + thoughts 23,736, and thoughts are not added to the cost a second time. Haiku's normalised reasoning=0 does not mean there was no internal computation. Provider-specific input counts also differ in tokenizer and in how the schema is passed, so we do not assert that the numerical differences are due solely to the tokenizer.

- Main evaluation, 90 cases: **USD 0.34594775**.
- Separate compatibility test, 6 cases: USD 0.00943500.
- Total for this work: **USD 0.35538275**.
- Cumulative including the earlier v1, v2, and their compatibility tests at USD 0.33626710: **USD 0.69164985**. Within the USD 5 limit.

The max/min ratio of input and output unit prices was 1.33 for each, but the max/min ratio of total main-evaluation cost was about 2.26. This is because actual usage differed, in particular Google's default thinking consumption. Therefore this experiment is **a comparison of candidates with similar unit prices**, not a comparison that controls actual cost or internal computation to be equal.

## 5. Draft results text for the thesis

"For three candidates with similar public API unit prices, we conducted an additional formative evaluation of 30 existing author-reference items each, 90 runs in total. Valid responses numbered 27 for GPT-5.4 Mini, 22 for Claude Haiku 4.5, and 30 for Gemini 3.8 Flash. The frozen selection rule excluded any candidate with a missed critical defect or with no valid evaluation for the relevant item. Only Gemini 3.8 Flash met this condition; it detected all 10 critical defects and showed 25/30 agreement with the author reference on overall pass/fail verdicts. However, it classified 5 of the 20 items the author judged fail as pass. The estimated cost of the main evaluation based on recorded usage was USD 0.34594775 in total. Although unit prices were similar, execution costs per candidate were not equivalent because of differences in default reasoning settings and actual output volume."

This result has the limitations of a single author reference, constructed items that share source material, and a comparison that reused the same material after seeing earlier results. It is not generalised to an overall provider performance ranking or to a confirmatory result on new material. Role-specific production model candidate selection and the provider independence of the final evaluator are separate decisions.

## 6. Reproduction materials and next steps

- Official same-day prices, URLs, capacities, and selection background: 20_MODEL_PRICE_AND_SELECTION_EVIDENCE_2026-09-05.md (Korean-language record; not linked).
- Frozen configuration/plan: ../19_EVALUATOR_PRICE_MATCHED_CONFIG.json, ../19_EVALUATOR_PRICE_MATCHED_PROTOCOL.md.
- Code: ../tools/v3/; freeze, access, and smoke receipts: ../private/v3/.
- 90 raw responses: ../private/v3/evaluator_results/.
- Canonical machine analysis: ../private/v3/evaluator_results_summary.json.
- Earlier comparisons: ../14_EVALUATOR_SELECTION_RESULTS.md, ../16_EVALUATOR_RERUN_V2_RESULTS.md. Preserved.

The next step is to reflect this result in finalising the candidates of the **unfrozen role-specific selection design** and the final-evaluator independence policy. No additional paid runs or application to the full pipeline were carried out in this work.
