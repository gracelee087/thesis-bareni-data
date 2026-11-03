# Data availability

## Included

- The files cited in the thesis text and appendices, at the same relative paths,
  except for the items listed under "Not included".
- The raw records of the final experiment STUDY-E-1 and of the supplementary
  comparison STUDY-E-ABLATION (folder `studies/study_e_ablaton/`), as listed in README.md.

## Not included

- Raw data from the earlier Study B pilots, because they contain third-party LinkedIn
  creator profile and post addresses. Summaries are in `studies/study_b/README.md`.
- The individual candidate outputs and scores produced during the pilot
  model-selection runs. The selection plans, results summaries and code are included;
  the summaries are appendix items L05–L07 in `studies/study_e_redesign/appendix/`.
- The records of the first STUDY-E-1 execution. Its results and the costs of both
  executions are reported in Appendix C.2 of the thesis.
- Working drafts, personal notes and credentials.

## What is unchanged and what was edited

- Unchanged: the raw data and the computed result values. Frozen files whose
  SHA-256 fingerprints are listed in the freeze lists are kept as written.
- Edited for this public copy: seven appendix documents (K02, K03, L06, L07, L08, L12
  and `studies/study_d/data/excluded_309138/README.md`). Personal notes were removed;
  their experimental content is unchanged.

## Notes for reading the records

- Retry extension in STUDY-E-ABLATION. During the run, the author approved an
  extension of technical retries, recorded in
  `studies/study_e_ablaton/private/retry_extension_user_authorized.json` and
  `retry_extension_transport_v2.json` (the `authorization` fields and the file name
  record this approval). The extension:
  - extended retries after transient transport and validation failures,
    within the budget and a cap of 15,000 total attempts;
  - added a minimum interval of 1 second between dispatches and a 30–60 second
    cooldown after a transient failure;
  - in the second record, also treated `RemoteProtocolError` as a retryable
    connection interruption.

  The retry record marks `scientific_settings_changed: false`. The USD 60 cap was
  retained, and earlier failures were preserved.
- Langfuse project and organisation identifiers appear in the telemetry records.
- Some frozen records contain Korean text. They are kept unchanged because their hashes
  are registered; English translations of the relevant lines are in
  [L11](studies/study_e_redesign/appendix/L11_prompt_korean_lines.md).
