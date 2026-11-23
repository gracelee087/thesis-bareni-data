# STUDY-E-1 online appendix materials

This folder holds the long materials that the thesis appendices point to but do not print in full. Tables and
figures stay in the thesis PDF. Every file here is in English. Files copied from elsewhere in the repository are
marked at the top; the originals and all frozen experiment records stay unchanged in their original locations.

| ID | File | Content | Source in this repository |
|---|---|---|---|
| L01 | [L01_selected_topics.json](L01_selected_topics.json) | The 125 selected topics | `../private/final125_v1/selected_topics.json` (identical copy) |
| L02 | [L02_persona.md](L02_persona.md) | Frozen reader persona | `../../study_d/config/persona_experiment.md` (identical copy) |
| L03 | [L03_company_evidence.md](L03_company_evidence.md) | Company evidence pack C01–C05 | `../../study_d/config/company_evidence.md` (two Korean file names replaced) |
| L04 | [L04_evaluator_rubric.md](L04_evaluator_rubric.md) | Independent evaluator instruction and four-dimension rubric | `../13_EVALUATOR_PROMPT.md` (identical copy) |
| L05 | [L05_evaluator_selection.md](L05_evaluator_selection.md) | Evaluator selection report (30 items, three candidates) | English translation of `../21_EVALUATOR_PRICE_MATCHED_V3_RESULTS.md` |
| L06 | [L06_role_selection_review.md](L06_role_selection_review.md) | Consistency review of the role-selection procedure | English translation of `../183_ROLE_SELECTION_METHOD_CONSISTENCY_REVIEW.md` |
| L07 | [L07_model_selection_history.md](L07_model_selection_history.md) | Model selection chronology | English translation of `../213_MODEL_SELECTION_CHRONOLOGY.md` |
| L08 | [L08_protocol.md](L08_protocol.md) | Frozen STUDY-E-1 protocol | `../215_FINAL_EXPERIMENT_PROTOCOL_DRAFT_EN.md` (one Korean file name replaced) |
| L09 | [L09_aspredicted_310130.pdf](L09_aspredicted_310130.pdf) | AsPredicted #310130 non-anonymous PDF (registration not yet public on 2026-09-17) | `../ASPREDICTED_310130_vj7sk9.pdf` (identical copy) |
| L10 | [L10_results.md](L10_results.md) | STUDY-E-1 results report | `../RESULTS_FINAL_EXPERIMENT_1_20260908_EN.md` (identical copy) |
| L11 | [L11_prompt_korean_lines.md](L11_prompt_korean_lines.md) | English translation of the Korean text inside frozen records | New |
| L12 | [L12_code_readme.md](L12_code_readme.md) and this README | Description of the final experiment code; this README lists where the raw data are | `../tools/final125_v1/README_EN.md` (one Korean diagram label translated) |
| L15 | [L15_texts_natural.md](L15_texts_natural.md) | Natural condition: initial draft, final text and evaluator scores of all 125 tasks | Generated from `../private/final125_v1/tasks/SE-FINAL-N*.json` (records unchanged) |
| L16 | [L16_texts_mixed.md](L16_texts_mixed.md) | Mixed condition: source task, defect type, initial draft, final text and evaluator scores of all 125 tasks | Generated from `../private/final125_v1/tasks/SE-FINAL-M*.json` (records unchanged) |
| L17 | [figures/appendix_h/](../../../figures/appendix_h/) | Langfuse screenshots behind thesis Figures H-1 to H-4 | Original PNG files |
| L18 | [final_design_sample_size_review_v2/README.md](../private/final_design_sample_size_review_v2/README.md), [HISTORICAL_RATIONALE_CORRECTION.md](../private/sample_size_review_v1/HISTORICAL_RATIONALE_CORRECTION.md) | Sample-size review documents named in registration answer 7: prospective sensitivity review of the final design and correction of the historical rationale for N=125 | Original files in `../private/`, with their verified calculation outputs and the scripts in `../tools/` and `code/bareni_pipeline/` |

## Raw data (not copied)

| Content | Location |
|---|---|
| Frozen execution plan: per-task inputs, role prompts, model settings | [`../private/final125_v1/execution_plan.json`](../private/final125_v1/execution_plan.json) — contains Korean Gate rule text; see L11 |
| Topic inventory: 1,899 unique topics, 670 excluded, 1,229 remaining | [`../private/final125_v1/topic_inventory.json`](../private/final125_v1/topic_inventory.json) — Korean appears only in file paths; see L11 |
| Analysis outputs: analysis JSON, cost, latency, quality and text-metric CSV files, audit receipts | [`../private/final125_v1/reports_final_2026-09-08/`](../private/final125_v1/reports_final_2026-09-08/README.md) |
| Task ledgers: per-task inputs, texts, Gate results and evaluator scores (250 files) | [`../private/final125_v1/tasks/`](../private/final125_v1/tasks/) |
| Freeze record with SHA-256 hashes | [`../private/final125_v1/freeze.json`](../private/final125_v1/freeze.json) |
| Code of the final experiment (frozen; not edited) | `../tools/final125_v1/`; English description in [L12_code_readme.md](L12_code_readme.md) |

STUDY-E-ABLATON materials are in [`../../study_e_ablaton/appendix/`](../../study_e_ablaton/appendix/README.md).
