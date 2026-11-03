# Study E evaluator selection — frozen run 1 results

Date: 2026-09-05

## Outcome

All 90 scheduled candidate–item pairs have terminal records. There are 21 valid assessments, 34 schema/semantic validation failures, and 35 records labelled `transport_failure` by the frozen runner. The latter category includes 30 OpenAI HTTP 400 request-schema rejections, not merely network failures. There were 94 request attempts including retries; this is not 90 successful model evaluations.

The frozen selection rule returns **no selected candidate**. This run does not establish that the three models lack evaluation ability: implementation and environment failures prevent a complete candidate comparison.

| Candidate | Valid / 30 | Schema/semantic failures | Request/connection failures | Recorded USD |
|---|---:|---:|---:|---:|
| gpt-5.6-luna | 0 | 0 | 30 | 0.00000000 |
| claude-haiku-4-5-20251001 | 21 | 7 | 2 | 0.11996800 |
| gemini-3.5-flash-lite | 0 | 27 | 3 | 0.02903820 |
| Total | 21 | 34 | 35 | 0.14900620 |

Costs use recorded API usage and the frozen price table, not a reconciled provider invoice. USD 5 cap was not reached.

## Execution and integrity

- User authorized the previously described 90-assessment action with “do”. The runner received its configured confirmation argument.
- Preflight verified all frozen hashes, Python/SDK versions, three API-key presences, and zero existing terminal records.
- The initial sandbox invocation produced connection failures for schedule entries 1–5 (two Haiku, three Gemini). It was interrupted and resumed with approved external network access. These terminal records were retained and skipped on resume under the frozen failure policy; they were not replaced.
- No prompt, schema, model, author rating, schedule, or frozen implementation was changed during the run.
- Progress metadata and transport-error diagnostics were inspected during execution. Candidate judgments and schema-error details were opened only after all 90 pairs reached terminal status.
- The analyzer verified complete schedule coverage and a consistent freeze hash before writing the summary.
- Freeze SHA-256: `0f5be04b7da14cdf3be3bffb8484bdbd02c32032b872513afe005a5eb9dd668f`.
- Summary SHA-256: `21cd7caeaa073b4702155d43f5684db1b821ac2bdc395b3b960587cefdffc215`.

## Failure findings

### OpenAI request schema

All 30 requests were rejected with HTTP 400 because `critical_evidence_quote` was absent from the root `required` list. The local Pydantic field has `default=None`; the runner directly sends its generated JSON schema. These are integration failures before evaluation, not incorrect model judgments. The previous synthetic dry-run did not detect API schema incompatibility.

### Gemini version field

The 27 returned responses failed local validation because `schema_version` was `1.0`, whereas the frozen local contract requires `study-e-evaluator-rating-v1`. The remaining three records are the initial sandbox connection failures. The adapter's handling of the fixed-value schema constraint needs verification before attributing this pattern to candidate ability. Raw responses remain preserved; they were not repaired or counted as valid.

### Haiku

Of 28 returned responses, 21 were valid. Six failed because the primary critical dimension was not scored 1; one had a pass decision inconsistent with its scores or critical flag. Two records are initial sandbox connection failures.

Among the 21 valid responses, pass/fail agreement with the author reference was 15/21 (71.43%); six author-low items were passed, and no author-pass item was failed. One author-critical item (`EVAL-BLIND-021`) had a missed critical violation. Seven further author-critical items lacked valid assessments. Haiku therefore fails the frozen eligibility rule even apart from the network incident. These statistics describe the valid subset, not all 30 items.

For Luna and Gemini, the analyzer's zero false-negative counts have zero valid assessments as their denominator; they must not be interpreted as perfect detection.

## Next step

Preserve this run as an unsuccessful selection execution. Before any further paid selection run, correct and test provider schema compatibility, verify Gemini fixed-value handling, and document the revised execution setup in a separate version and freeze. Synthetic valid and invalid fixtures should exercise nullable required fields, fixed values, and cross-field rules. Any future use of the same 30 items must acknowledge that their model results have now been inspected. Do not combine a revised run with these records or advance to full Study E calibration on the basis of this run.

Raw records: `private/evaluator_results/` (90 files). Machine-readable analysis: `private/evaluator_results_summary.json`.
