> English translation prepared 2026-09-17 of `implementation_resolution.md`. The Korean original is the recorded/frozen document; where wording differs, the original governs.

# Implementation Follow-up After Price Reconciliation — 2026-09-07

README.md, pricing_audit.json, and manifest.json in the same folder are preserved as the record at the time of the 08:29 UTC reconciliation. The unresolved Gate reservation value and the service-tier confirmation status in that record were updated by the follow-up implementation below. The target files of the original manifest were not modified.

- Single configuration: `../../pricing.json`. The five official base rates for input, cache, and output were kept as they were. Only the Gate's `cache_write_input` was changed from 3.125 to 2.5 to match the Curator. This does not mean OpenAI charges a separate write surcharge; it is a reservation-compatibility field.
- Standard requests: OpenAI `service_tier=default` is specified explicitly, and a different tier in the response halts execution as cost-unconfirmed. Execution halts if the price file or plan hash differs or if the Gemini introductory rate has expired.
- Observed cost: the same price computation is applied to the actual response usage of successes and validation failures. Cache read/write and visible output/thinking are separated without duplication. Anthropic 5-minute/1-hour cache writes are distinguished. For GPT-5.4, the long-context rate applies when total input **exceeds** 272,000 tokens (exactly 272,000 is the base tier). The original README's wording "under 272K" is corrected to this exact boundary.
- Langfuse: the five custom models were registered in the new project in USD per token and read back. Local cost line items are sent directly to generations, without relying on Cloud automatic estimation. The verification receipt is `../../langfuse_pricing_verification_2026-09-07.json`.
- Actual Cloud verification: usage, itemized cost, ERROR, and verification descriptions were read back for 7 synthetic generations. They were marked with the `pricing-verification` environment and `synthetic=true`, `exclude_from_experiment=true`. Model provider calls 0, actual provider billing 0 dollars. Synthetic costs are not experiment expenditure.
- Error recording: API/response validation failures are left as ERROR. Cost-unconfirmed tokens are left only in metadata to prevent incorrect Cloud cost estimates. Content defects are left in the Gate result, and transport failures are recorded in local telemetry_events.

The execution code, plan, and protocol before modification are preserved in `../../pricing_changes/20260907T094222/before/`. The final offline check is confirmed by the time-stamped receipts pointed to by `../../offline_test_receipt.json`. Experiment tasks, order, defect assignment, model selection, and the 49.99-dollar cap were kept.

This is a verification of official public rates; actual invoice, account credit, and tax reconciliation was not performed. Screenshots of the official pages, estimation of expected total cost for the two conditions, the final freeze, and AsPredicted registration are still incomplete.
