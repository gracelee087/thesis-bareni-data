# Excluded AsPredicted #309138 execution

- Registration: AsPredicted #309138 (`https://aspredicted.org/8iq2yy.pdf`).
- Confirmatory namespace: `SD-291` through `SD-415`.
- Disposition: terminated and excluded before a fresh preregistration.
- Observed state at termination: 2 complete records (`SD-291`, `SD-292`), 5 recoverable task-attempt records, 0 closed batches, and no hypothesis analysis.
- Locally attributable LLM cost after reconciliation: USD 0.77393475.
- `SD-293` interruption reconciliation: Langfuse trace `375d20eae331749329e4de0ba2c082c2` confirms one successful Planner call costing USD 0.00151425 under the frozen price snapshot. A Researcher request may have been in flight when the process was interrupted, but no provider response or Langfuse generation record was available; no tokens or cost were invented for it.
- A later attempted restart created one zero-cost `SD-293` transport-failure record (`b2-final-SD-293-5ef6d48f6253`) before any new paid call.

Nothing in this directory may enter the replacement study's H1, H2, H3, task bank, lesson state, or cost ledger. The files are retained only as an audit trail.
