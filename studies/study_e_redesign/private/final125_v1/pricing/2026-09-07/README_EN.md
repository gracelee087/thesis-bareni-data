> English translation prepared 2026-09-17 of `README.md`. The Korean original is the recorded/frozen document; where wording differs, the original governs.

# Study E Model Official Rate Reconciliation — 2026-09-07

The official standard API prices and the current execution configuration **match in all input, cache-read, and output rates**. Unit: USD / 1 million tokens. These are not subscription fees or provider Batch discount prices.

| Provider | Model | Role | Input | Cache read | Output |
|---|---|---|---:|---:|---:|
| Anthropic | claude-haiku-4-5-20251001 | Planner | 1.00 | 0.10 | 5.00 |
| Anthropic | claude-opus-5 | Researcher | 5.00 | 0.50 | 25.00 |
| OpenAI | gpt-5.4-mini | Writer / Critic / Optimizer | 0.75 | 0.075 | 4.50 |
| OpenAI | gpt-5.4 | Gate / Lesson Curator | 2.50 | 0.25 | 15.00 |
| Google | gemini-3.8-flash | Independent evaluator | 0.75 | 0.075 | 3.75 |

Official sources: [Anthropic model pricing](https://platform.claude.com/docs/en/about-claude/pricing), [OpenAI API pricing](https://developers.openai.com/api/docs/pricing), [Google Gemini 3.8 Flash pricing](https://ai.google.dev/gemini-api/docs/pricing#gemini-3.8-flash).

## Conditions and Caching

- Anthropic's 5-minute/1-hour cache writes are Haiku 1.25/2.00 and Opus 6.25/10.00. Current requests have no cache_control, and cache read/creation tokens are computed according to response usage. Opus's US-only inference is a surcharge condition, but no inference_geo is currently specified.
- GPT-5.4 and Mini have no separate cache-write surcharge. The 1.25× write rate applies from GPT-5.6 onward. [Official cache documentation](https://developers.openai.com/api/docs/guides/prompt-caching)
- The base tier in the GPT-5.4 table is for contexts under 272K, and the long-context tier is input 5.00/cache 0.50/output 22.50. Other service conditions such as regional processing and Fast are subject to separate confirmation.
- Gemini prices are introductory rates through 2026-12-31. From 2027-01-01, input 1.50/cache 0.15/output 7.50 are scheduled. Output includes thinking tokens, and the code sums these as well. Explicit cache storage is currently 0.50 per 1 million tokens per hour, but the current evaluation requests do not create storage resources.

## One Remaining Item from the Code Reconciliation

For the same GPT-5.4 in `private/final125_v1/execution_plan.json`, the Gate's `cache_write_input` is 3.125 and the Curator's is 2.5. The former is not GPT-5.4's official additional cache-write rate.

`tools/gate_v5/run_gate_selection.py` sets write=0 in the OpenAI observed-cost computation, so this value is not directly reflected in observed cost. However, because reserve() uses max(input, cache_write_input), the Gate's **input reservation portion** is 25% higher than the normal input basis. This does not mean the total request cost or billed amount is 25% higher. The reservation rationale must be settled before freezing. Code and execution configuration were not changed in this price check.

## Verification Scope and Preservation Status

The model list, currently applied rates, SDK request paths, and cost and reservation functions were reconciled. The local SDK's OpenAI/Anthropic destinations are api.openai.com/api.anthropic.com respectively, and no separate gateway configuration was found. These are ordinary synchronous calls and do not use provider Batch APIs. The study's four batches are not computed at provider Batch discounts.

This record is a verification of official public rates and not an actual invoice reconciliation. Account discounts, credits, taxes, Google billing tier, and the default service tier in provider consoles were not independently verified this time. Paid model calls: 0.

Captures of the official pages are preserved in `screenshots/`. The planning estimate obtained by extending the actual usage ledger of the preserved 125-task pilot to the scope of the current two conditions is natural $19.3603 + mixed $11.0603 = **$30.4206** (including the mixed condition's reserve for unconfirmed usage of $3.9144). Thus $19.5694 of planning headroom remains within the $49.99 cap. This is neither a provider invoice nor a guaranteed cap, and it will vary with actual output volume, failures, and retries. The computation is preserved in `expected_cost_estimate.json`.

`pricing_audit.json` contains the mechanically reconciled per-role figures, official URLs, verification time, code hashes, and incomplete items. `manifest.json` is an integrity index of these price-reconciliation files and not a manifest that freezes the experimental conditions.

Reconciliation completed (UTC): 2026-09-07T08:29:42.535229+00:00

Reconciliation completed (Europe/Berlin): 2026-09-07T10:29:42.535229+02:00
