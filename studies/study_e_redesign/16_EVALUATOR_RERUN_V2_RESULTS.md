# Study E evaluator selection — v2 results

Date: 2026-09-05. Outcome: **gpt-5.6-luna selected under the frozen rule**.

## Execution and selection

The corrected run completed all 90 scheduled pairs: 30 per candidate. There were 79 valid assessments and 11 semantic validation failures. No request/connection failures or schema-version failures occurred. The analyzer verified the complete candidate–item schedule and matching freeze hashes before unblinding.

| Candidate | Valid / 30 | Critical misses among valid | Author-critical items unscored | False negatives among valid | False positives among valid | Semantic failures | Recorded USD |
|---|---:|---:|---:|---:|---:|---:|---:|
| gpt-5.6-luna | 30 | 0 | 0 | 3 | 1 | 0 | 0.01978480 |
| claude-haiku-4-5-20251001 | 23 | 1 | 4 | 7 | 0 | 7 | 0.12887200 |
| gemini-3.5-flash-lite | 26 | 2 | 2 | 7 | 0 | 4 | 0.03257180 |

Luna is the only eligible candidate: it returned a valid rating for every author-critical item and missed none of the ten critical violations. Haiku and Gemini fail the first selection gate. Selection therefore does not require the cost or latency tie-breakers.

Luna pass/fail agreement was 26/30 (86.67%). It passed three of the 20 author-low items (15% false-negative rate) and failed one of the ten author-pass items (10% false-positive rate). These are descriptive rates on this small constructed set.

- False negatives: EVAL-BLIND-019, 024, 027.
- False positive: EVAL-BLIND-018.
- Dimension score exact agreement: 79/120 (65.83%).
- Dimension scores within one point: 112/120 (93.33%).
- Mean absolute dimension error: 0.4417.
- Mean cost per valid assessment: USD 0.00065949.
- Median request latency: 5.796 seconds.

For Haiku and Gemini, error counts in the table describe only valid responses; missing/invalid responses are reported separately and are not treated as correct judgments.

## What failed

Haiku's seven invalid responses comprised four critical-dimension score inconsistencies, two pass/score inconsistencies, and one score-total mismatch. Gemini's four invalid responses comprised two critical-dimension score inconsistencies and two pass/score inconsistencies. They were not repaired or retried.

The v1 OpenAI required-field and Gemini fixed-version failures did not recur. The actual six-call synthetic serialization test passed before this run; it tests API compatibility, not evaluation quality.

An overbroad operational guard temporarily treated semantic errors as version errors because Pydantic includes schema_version in its input-value preview. A separate supervisor resumed only after recognizing known semantic errors and skipped existing terminal records. The frozen runner and all requests were unchanged. This is documented in 15A_V2_STOP_GUARD_NOTE.md and is an implementation limitation of this runner version.

## Cost and preserved records

| Component | Recorded USD |
|---|---:|
| Previous unsuccessful run | 0.14900620 |
| Six synthetic compatibility checks | 0.00603230 |
| v2 selection run | 0.18122860 |
| This rerun task, including compatibility checks | 0.18726090 |
| Cumulative across both runs and checks | 0.33626710 |

These are API-usage estimates using the frozen price table, not reconciled provider invoices. The cumulative amount remains below USD 5.

- v2 freeze SHA-256: 8380354970c842393972415ade7180cd5551caf6a6f3712c654cbd8d38b80d69.
- Summary SHA-256: a55688614fbc61722ca1b8ffa2f8302d1cfb86650195e4e58ecb2cba390db1d6.
- Raw v2 records: private/v2/evaluator_results/ (90 JSON files).
- Analysis: private/v2/evaluator_results_summary.json.
- Synthetic checks: private/v2/smoke/ and private/v2/smoke.json.
- Original failed run and its frozen code remain preserved separately.

## Scope and next step

This selects an evaluator for the Bareni formative workflow under the recorded prompt, rubric, author reference, API defaults and candidate list. It does not establish universal superiority or external human validity. The same 30 items were reused after run 1 results had been inspected; this rerun is disclosed implementation correction, not independent confirmation. Zero critical misses in ten constructed critical items does not prove a zero future miss rate.

Use Luna as the selected outcome-evaluator candidate when designing the next role-selection stage. Preserve the three false-negative examples and one false-positive example as limitations; do not silently tune the rubric or prompt to erase them. Writer/gatekeeper/critic/optimizer selection and separate full-pipeline calibration remain outstanding. This task did not execute those stages.
