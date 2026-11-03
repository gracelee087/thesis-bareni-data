> English translation prepared 2026-09-17 of `RESULTS_KO.md`. The Korean original is the recorded/frozen document; where wording differs, the original governs.

# STUDY-E-ABLATON Results

A separate follow-up comparison reusing the 125 mixed initial inputs of STUDY-E-1. Three replicates per task, and both Optimizers receive Gate information directly. It examines the incremental effect of Critic instructions and is not pooled with the H1–H3 results of the existing final experiment.

Completed evaluations: 750/750. Physical API attempts: 3054. Known cost computed from usage: USD29.50648524. Provider invoice reconciliation is incomplete.

| Item | Critic on | Critic off |
|---|---:|---:|
| Mean total score (4–20) | 19.7493 | 19.6987 |
| Final low quality | 2/375 | 4/375 |
| Production cost (including half of shared Gate) | USD11.965909 | USD10.747754 |

The overall mean of the per-task 3-replicate mean difference (Critic on − off) is 0.0507 points. The two-sided p of the task-level sign-flip test is 0.180588, and the 95% t reference interval is [-0.0197, 0.1210].

The result is confined to the fixed mixed inputs and this controlled structure. It is not interpreted as 750 independent topics and is not generalized to the natural condition or the full multi-agent structure. A non-significant result is not proof of equivalence or absence of effect.

Input, result, and analysis integrity checks passed: True. All logical calls recovered: True. Usage for the 10 communication-failure attempts was preserved as unconfirmed, and the reserve of USD0.63653450 was included in the limit calculation. Unconfirmed cost is not assumed to be 0. For the full Langfuse reconciliation, see the separate cloud_audit receipt.

Full Langfuse reconciliation: request, response, model, status, usage, and cost records for 3,054 attempts match. Unrecovered logical calls: 0. Cloud reconciliation is separate from provider invoice finalization.
