# Thesis figure assets

`tools/render_thesis_figures.py` creates the reproducible figure set in this directory.
Seven figures, each rendered in Korean (`-ko`) and English (`-en`), as SVG and PNG.

| Figure | File stem | Source |
|---|---|---|
| 4-1 Company-level structure | `figure-4-1-company-structure` | Section 4.2 of the manuscript |
| 4-2 Shared specification frame (5 departments x 5 columns) | `figure-4-2-common-skeleton` | Sections 4.2 and 4.3.1 |
| 4-3 Two executed loops and unimplemented company-level learning | `figure-4-3-three-loops` | Section 4.2.1 |
| 4-4 The executed Marketing task graph | `figure-4-4-marketing-task-graph` | Section 5.4 and the frozen run configuration |
| 5-1 Production-cost distribution | `figure-5-1-production-cost` | `studies/study_d` — 125 task records |
| 5-2 Paired low-quality transitions | `figure-5-2-h3-transitions` | `studies/study_d` — 125 task records |
| 5-3 Routing comparisons and Study D | `figure-5-3-study-design-comparison` | Section 5.10; conditional-refinement and forced-refinement comparisons (originally Experiment A/B), and Study D |

SVG files are the manuscript assets. PNG files are 300-DPI inspection copies.

Run from the repository root:

```powershell
python tools\render_thesis_figures.py
```

## Provenance of the empirical figures

Figures 5-1 and 5-2 read the sealed confirmatory study (AsPredicted #309181):
`studies/study_d/data/runs/*.json` for the per-task production cost, refinement count
and blinded-evaluator judgments, and `studies/study_d/data/batch_journal/*_lesson_close.json`
for the batch lesson-extraction cost, which the registered H2 accounting spreads evenly
across that batch's tasks.

The script recomputes the H2 total, mean and coefficient of variation and the four H3
transition counts from those raw files, and **refuses to draw anything** unless they match
`studies/study_d/data/analysis/final_analysis.json` to within floating-point tolerance.
Nothing plotted is hard-coded.

## Superseded figures

Earlier drafts carried one interface diagram per department (`figure-4-2-strategy`,
`4-4-operations`, `4-5-finance`, `4-6-self-management`), a hand-off envelope diagram
(`4-7`), and Chapter 5 figures built from the previous experiment
(`studies/study_b/b2_final_2026_terra_n125`). They also temporarily departed from the
Proposal's definition of the fifth department. Those assets were removed or superseded
on 2026-09-04; the current figures restore the five
Proposal departments and point the empirical plots at Study D (#309181). Earlier assets
remain recoverable in git history.
