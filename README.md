# Thesis materials: Bareni multi-agent marketing evaluation

This repository holds the materials for the master's thesis
"A Reference Architecture for Multi-Agent Augmentation of Solo Entrepreneur Business
Operations, with Telemetry-Based Evaluation of the Marketing Department"
(Sohee Lee, Frankfurt School of Finance & Management, Master in Data Analytics & Management).

The materials included here keep the relative paths cited in the thesis.
Items that are not included are listed in [DATA_AVAILABILITY.md](DATA_AVAILABILITY.md).

## How the folders are organised

| Role in the thesis | Folder | What it contains |
|---|---|---|
| Design history (Studies A–D, Experiments A–B) | `studies/study_a` … `studies/study_d` | Summaries of earlier designs (L14). Study D also keeps its configuration and results record. |
| Pilot (model selection) | `studies/study_e`, and the selection records in `studies/study_e_redesign/` | Summary of Study E, role-by-role model selection plans, results summaries and code (L05–L07). |
| **Final empirical test: STUDY-E-1** (AsPredicted #310130) | `studies/study_e_redesign/private/final125_v1/` | Frozen protocol and freeze list, registration receipt, 250 task ledgers, 1,860 call starts and 1,860 call results, 250 production records, pricing evidence, final reports and the Langfuse reconciliation. |
| Supplementary comparison: STUDY-E-ABLATION (recorded as `STUDY-E-ABLATON` in the files) | `studies/study_e_ablaton/` | Protocol, code, 6,108 ledger files, 3,054 Langfuse telemetry records, 750 evaluations, 375 pairs and the cloud audit (K01–K03). |
| Figures | `figures/` | Figures used in the thesis. |

## Where to start

| Thesis item | Location |
|---|---|
| Appendix index (L01–L17) | [studies/study_e_redesign/appendix/README.md](studies/study_e_redesign/appendix/README.md) |
| Final experiment STUDY-E-1 | [studies/study_e_redesign/](studies/study_e_redesign/) |
| Supplementary comparison STUDY-E-ABLATION (K01–K03) | [studies/study_e_ablaton/appendix/README.md](studies/study_e_ablaton/appendix/README.md) |
| Research history summaries (L14) | `studies/study_a` to `studies/study_e` README files |
