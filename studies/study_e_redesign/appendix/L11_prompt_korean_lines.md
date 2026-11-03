# L11. English translation of the Korean text inside the frozen STUDY-E-1 records

Most STUDY-E-1 records are in English. A few frozen records contain Korean text. These records were hash-locked
before execution (`../private/final125_v1/freeze.json`), so they are **not edited**. This page gives an English
translation of every Korean passage in them, identified by rule ID and bullet order. The original Korean text is
what was actually stored or sent; the English below is a translation for readers only (prepared 2026-10-16).

## 1. Gate rule text in the frozen execution plan

File: `../private/final125_v1/execution_plan.json` (SHA-256
`075012aade3b2f51d059bbef9744a1cbdb0dcef2ad6e3fa04557ca846dc804ed`, listed in `freeze.json`). The Korean passages
are in `templates.gate.rules` (rule IDs R-N-1 to R-N-4 and R-C-1 to R-C-3). The same rule text is repeated inside the
stored example Gate request (line 10827). These rules were part of the **Gate** (routing) prompt. The independent
evaluator used the English rubric in `L04_evaluator_rubric.md`.

### R-N-1 to R-N-4 (Persona Fit, Clarity, Actionability, Factual Grounding)

Each of these four rules begins with a two-word Korean label meaning **"Evaluation question:"**, followed by an
English question. The rest of the four rules is already in English.

### R-C-1 — 4.1 Factual critical violations

| Bullet | English translation |
|---|---|
| 1 | Inventing or implying a non-existent customer, customer project, testimonial, deployment, or customer result. |
| 2 | Presenting a self-built demo or prototype as a customer case or a production system. |
| 3 | Presenting synthetic data or a calculation model as actually observed values. |
| 4 | Presenting AP's €473k as actual savings or as a Bareni result. |
| 5 | Presenting an unimplemented function as working. Examples: AP's PDF/OCR/3-way match; Atlas's direct Google Calendar/Meet integration; billing; self-service or multi-customer operation. |
| 6 | An unverified sweeping legal claim. Example: asserting that a specific act is always illegal in Germany. |
| 7 | Claiming a thesis result, customer effect, revenue effect, or multi-agent superiority that the current experiment has not verified. |

### R-C-2 — 4.2 Persona critical violations

| Bullet | English translation |
|---|---|
| 1 | Presenting German customers or a German-language service as the current target/service. |
| 2 | Actively selling work that is explicitly not accepted, such as sensitive medical, legal, or financial work, bulk cold email, or OCR-centred work. |
| 3 | Using a real name, face, or the founder's career history as a basis of authority. |
| 4 | Presenting Bareni as a legally registered company, a multi-person team, or a business that already has a customer track record. |

### R-C-3 — 4.3 Actionability critical violations

| Bullet | English translation |
|---|---|
| 1 | Recommending that AI carry out approvals that move money, or high-risk decisions, without human approval. |
| 2 | Recommending to the reader an action that clearly conflicts with the current engagement boundaries. |

## 2. Korean file and folder names in the topic inventory

File: `../private/final125_v1/topic_inventory.json`. The Korean text in this file consists only of file paths: the
author-written topic bank file (a file name meaning "Topics"), from which the 125 topics were selected, and one
historical Study B folder name meaning "choosing an LLM", which appears only as a compared input path. The selected
125 topics are in English (`L01_selected_topics.json`).

The freeze record `../private/final125_v1/freeze.json` contains the same topic-bank file name once, as the key of
its SHA-256 hash entry.

## 3. Appendix copies whose Korean file names were replaced

- `L03_company_evidence.md` copies `../../study_d/config/company_evidence.md`. Its status note named two
  Korean-titled source documents of the author (a project checklist and company-and-persona Q&A notes). In the copy,
  these names are replaced by English descriptions. The original file is unchanged.
- `L08_protocol.md` copies `../215_FINAL_EXPERIMENT_PROTOCOL_DRAFT_EN.md`. In the copy, the Korean topic-bank file
  name is replaced by an English description. The original document keeps the earlier wording.
