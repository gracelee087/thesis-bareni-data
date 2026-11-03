> English translation prepared 2026-09-17 of `OPERATIONS.md`. The Korean original is the recorded/frozen document; where wording differs, the original governs.

# Operational Changes During Execution

2026-09-08: Transient communication failures and response validation failures were extended to be retried after waiting, within the budget limit. This is the part changed from the original plan's limit of 3 technical retries per call. The original plan and FREEZE.json are preserved.

- Execution: `python studies/study_e_ablaton/resume.py`
- Initial inputs, models, prompts, 3 replicates per task, the comparison of the two groups, the maximum of 2 semantic revisions, and the evaluation and analysis rules are unchanged.
- The API request start interval is kept at a global minimum of 1 second, with a 30–60 second wait after a transient failure.
- Successful responses use the stored copy. Failure records are preserved, and reserves for attempts with unclear usage continue to be included in the cost limit.
- Automatic retries also run only within the USD60 and 15,000 total-attempt limits. Integrity problems such as input mismatch or model mismatch are not treated as success.
- Approval and code hashes are recorded in private/retry_extension_user_authorized.json. This is not represented as a change to an external preregistration.

Subsequent fix: RemoteProtocolError was classified as a transient connection interruption and retried. The existing operational code and approval are preserved in resume_v1.py and the original approval JSON, and the v2 change was recorded in private/retry_extension_transport_v2.json. 4 verifications passed, including an offline test reproducing that failure, and the actual evaluation also succeeded on retry. All 3,037 logical calls completed with valid responses, and the total number of physical attempts is 3,054.
