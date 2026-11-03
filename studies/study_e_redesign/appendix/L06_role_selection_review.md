> English translation of `../183_ROLE_SELECTION_METHOD_CONSISTENCY_REVIEW.md` prepared for the thesis appendix (2026-10-16). The Korean original is unchanged and remains authoritative for wording.

# Procedural consistency review of Researcher, Lesson Curator and Critic

2026-09-06. Because performing some verifications for one role but omitting them for another is not acceptable, the existing plan, execution and audit records were compared. This document is a post-hoc procedural review; it is not a new preregistration or a revision of raw scores. New paid calls: 0.

The common execution and judgement principles are consistent, but the development paths and completion records are not identical. It must not be stated that every role went through the same independent fresh-item final validation. At the same time, it cannot be concluded that there was a violation of the pre-specified procedure merely because the number of additional steps differs by role.

| Step | Researcher | Lesson Curator | Critic |
|---|---|---|---|
| Role criteria, inputs and references fixed in advance | 97, 105, etc. | 116, 124, 126 | 116, 124, 125 |
| Synthetic compatibility check → main test | Performed | Performed; failing candidate stopped early | Performed |
| Content audit, raw-output preservation, freezing | Performed | Performed on 12 valid GPT outputs | Performed on 24 outputs from the two candidates |
| Candidate expansion | Mini/Haiku→GPT/Sonnet→Opus | Mini/Haiku→GPT/Sonnet | No expansion, since the initial two candidates were eligible |
| Prompt revision targeting output meaning | Performed: 138, 139 | None in the subsequent path checked | None |
| API representation revision | Initial ID-contract supplement etc., recorded separately | 146: equivalent-representation revision of a nullable enum | Executed with the native ID contract included from the start |
| Separate fresh items after revision | 621–632 prepared via 159; the same set reused for later candidates | No separate fresh item set | No separate fresh item set |
| Latest role judgement | Opus5 eligible, selection recorded in 181 | GPT-5.4 eligible (157); single-assignment record not completed | Mini and Haiku eligible (144); single-assignment record not completed |
| Actual inter-role integration test | Not conducted | Not conducted | Not conducted |

**Basis for the additional steps.** The Researcher had a judgement procedure added to its system prompt after the earlier failures. 138 treated the before/after difference on the same items only as a development result and required a separate fresh-item validation, and 159 carried this out. The Critic passed with its initially frozen prompt. Curator 146 changed a nullable enum that the API had rejected into a representation of the same allowed values, which is distinct from a step that revises the semantic prompt to fit the answers it had failed. Therefore the difference in fresh-item validation has a methodological reason. 97 and 116 did not require a separate final fresh-item set common to all roles.

**Principles kept in common.** Pre-specifying role-specific criteria, checking inputs/references, freezing the exact request and settings, synthetic checks, a single attempt with 0 retries, stopping after a format/transport failure in that run, distinguishing machine validity from content pass, preserving the human rater's scores, and not overwriting failure records with success results. Expansion after a failing candidate branched according to whether the role had an eligible candidate. The Critic's criterion of repairing targeted defects / leaving normal items unmodified and the Researcher's and Curator's full-satisfaction criterion are differences that follow from the purpose of each role, and there is no reason to force them to the same number.

**Parts where inconsistencies or limitations must be disclosed.**

- The model-name blinding of the initial plan was not maintained in the subsequent single-candidate stages. Curator 157 and Researcher 159, 170 and 177 disclose that they are audits in which the candidate was known. Shuffling the item order does not substitute for model-name blinding.
- The candidate expansion and the choice of Opus are sequential development decisions that followed earlier results and subsequent decisions. They are not to be described as a comparison in which all candidates and the stopping order were fixed in advance in the initial plan. The exclusion of Opus at the time of plan 127 and its later explicit addition in 177 are recorded as stage-by-stage scope changes.
- The Researcher's fresh items were also written by an AI that knew the existing error types, and they were reused for Sonnet/Opus after the GPT results. They are not to be called an external independent confirmatory set.
- The failure to report each role's 'development eligibility', 'operational model assignment' and 'full-path validation' status in a uniform way needs to be cleaned up. If one speaks as though the Curator, despite having passed its criteria, still necessarily has an additional fresh-item validation outstanding, that would be adding post hoc a condition that is not in the existing 116.
- The Critic retained two eligible candidates in accordance with the pre-specified principle. If a single final one is chosen, the operational reasons such as accuracy, cost and latency must be stated, and it must not be written that only the selected model passed the test.

**Common handling principles going forward.** The role-eligibility judgements made under the existing plans are preserved as they are, and for all three roles the eligible candidates, the selected model, the exact settings and the not-yet-conducted integration validation are recorded in the same format. Cases where the semantic prompt was revised after a failure are distinguished from semantically equivalent API-compatibility revisions. If it is decided that an additional test is needed, its purpose and target role are stated before any call. To introduce a final fresh-item test as a new common condition for all roles, it must be applied to all three roles; the Researcher's already-used 621–632 alone are not reclassified as an independent final test that satisfies it. The present review by itself does not add any new global condition or paid test.

Sources of results: ../97_PLANNER_RESEARCHER_COMPARISON_PLAN.md, ../116_CRITIC_MEMORY_COMPARISON_PLAN.md, ../127_RESEARCHER_NEXT_TIER_PLAN.md, ../138_RESEARCHER_PROCEDURE_DEVELOPMENT_PLAN.md, ../144_CRITIC_SELECTION_RESULTS.md, ../145_CRITIC_AUDIT_NOTES.md, ../146_CURATOR_SCHEMA_DIAGNOSIS_AND_PLAN.md, ../149_CURATOR_DECISION_AND_NEXT_CANDIDATES.md, ../157_CURATOR_NEXT_TIER_SELECTION_RESULTS.md, ../159_RESEARCHER_GPT54_FRESH_VALIDATION_PLAN.md, ../170_RESEARCHER_SONNET5_VALIDATION_PLAN.md, ../177_RESEARCHER_OPUS5_VALIDATION_PLAN.md, ../181_RESEARCHER_OPUS5_SELECTION_RESULTS.md.
