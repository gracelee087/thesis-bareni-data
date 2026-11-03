# Study E — Proposal-literal arms A and B: results (exploratory, appendix material)

Generated 2026-09-01 from `arm_a/data/analysis/final_analysis.json` and `arm_b/data/analysis/final_analysis.json`
(schema `study-e-proposal-literal-analysis-v1`). Both arms ran the 125 Study D topics SD-416–SD-540
(bank files byte-identical to #309181), 31/31/31/32, in one afternoon (A 16:27–18:26, B 16:31–17:50 CEST),
with an empty lesson register at start and no Study D output read. Neither arm was registered on
AsPredicted; each was frozen and pushed to GitHub before its first paid call (A: commit 1668737,
manifest 6bf5c699…; B: commit 25b84fc, manifest cb00b358…). Measurement follows Proposal §9 literally:
the gate judge's own G-Eval assessment is the H3 instrument; no blinded evaluator exists.

## Three designs on identical topics

| | Study D (#309181, confirmatory) | Arm A (Figure 1 reading) | Arm B (§9-sentence reading) |
|---|---|---|---|
| Refinement trigger | Critic→Optimizer always once; gate decides pass 2 | same as D | gate on the draft decides whether Critic→Optimizer run at all |
| H3 instrument | blinded claude-opus-5 (gate reported as contrast) | gate judge gpt-5.6-luna | gate judge gpt-5.6-luna |
| H1 completion | 125/125 PASS | 125/125 PASS | 125/125 PASS |
| H2 production cost, mean / total (USD) | 0.0258 / 3.22 | 0.0261 / 3.27 | 0.0142 / 1.77 |
| H2 CV (bootstrap 95%) | 0.185 (0.140–0.229) **PASS** | 0.187 (0.160–0.208) **PASS** | 0.660 (0.572–0.739) **FAIL** |
| Refinement passes 0 / 1 / 2 | 0 / 121 / 4 | 0 / 122 / 3 | 87 / 35 / 3 |
| H3 low-quality draft → final | blinded 18 → 0 (100%) PASS; gate contrast 23 → 0 | gate 37 → 1 (97.3%) PASS | gate 36 → 0 (100%) PASS |
| Wilcoxon (paired totals, two-sided) | p = 1.3e-10 (secondary) | p = 5.2e-16 (primary) | p = 2.3e-09 (primary) |
| Exact McNemar | 7.6e-06 | 2.9e-11 | 2.9e-11 |
| Gate total 4–20, draft → final | 15.20 → 17.11 | 14.97 → 17.25 | 15.06 → 16.36 |
| Failed provider attempts (all auto-recovered) | 28 | 32 | 10 |
| Measurement cost outside H2 (USD) | 25.88 | 0 | 0 |
| Median task latency | 97 s | 42 s | 19 s |
| Words draft → final | 78.4 → 68.3 | 79.4 → 69.0 | 79.1 → 75.3 |

## What the comparison shows

1. **Replication.** Arm A reproduces Study D's operational profile on the same topics without the
   blinded evaluator: identical routing yields the same completion, the same cost level and the same
   cost variability (CV 0.187 vs 0.185), and a comparable share of second passes (3 vs 4).
2. **The refinement trigger drives H2.** Reading §9 as a conditional trigger (arm B) cuts production
   cost by 46% but splits tasks into three cost strata (0 passes USD 0.0086, 1 pass 0.025, 2 passes
   0.048) and raises the CV to 0.66, failing the preregistered criterion. This is the same pattern as
   the superseded SB2F study (CV 0.415) and the Study D pilot (0.524), now observed on the Study D
   topics themselves.
3. **Gate-measured H3 is circular.** With the routing judge as instrument, H3 is 97–100% in every arm
   because the loop stops exactly when that judge passes a text. Study D's blinded 18 → 0 is the
   non-circular figure; the gate contrast in Study D (23 → 0) sits at the same level as arms A and B.
4. **Draft quality is not a property of the topic.** Among the 125 shared topics, the drafts the gate
   marked low overlap only partly across arms (D∩A 9, D∩B 10, A∩B 12 of 23–37), so the paired
   comparison is between designs, not between fixed hard and easy topics.

## Boundaries

Exploratory and unregistered; the confirmatory verdicts remain those of #309181. Both arms share
the Study D models, prompts, rubric, gate rule, lesson architecture and analysis code; the only
differences are the absence of the blinded evaluator, the Wilcoxon test as the named primary test,
and (arm B) the conditional trigger. Lesson trajectories are descriptive (A: 2→3→4 active lessons;
B: 2→3→4→4). Costs use the same frozen prices as Study D; OpenAI cache-write tokens are billed at
1.25× input as on the provider's price page.
