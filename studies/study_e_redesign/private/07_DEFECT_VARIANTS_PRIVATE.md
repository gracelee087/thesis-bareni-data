# Study E evaluator selection — private defect variants

Status: drafted from allocation frozen in commit `12567ee`
Date: 2026-09-05

Do not show this file to the author-rater before the first 30-item rating and immediate 10-item rerating are frozen. Titles are preserved from the corresponding normal source. Intended labels are construction checks; the later author reference rating determines the comparison labels.

## EVAL-SRC-01

### Subtle variant

- Intended target: Persona Fit = 2; critical = false
- Title: `Start with one workflow, not a platform`
- Body (425 characters): `Enterprise-wide automation begins with a transformation programme aligned across functions, platforms and scalable operating priorities. Select one recurring task as the first workstream, then agree scope, price, duration and success measure before building. A small working version comes first, followed by a scoped pilot and later expansion. Write down one task you repeat every week and the number that would mark success.`

### Critical variant

- Intended target: Factual critical — fabricated customer result
- Title: `Start with one workflow, not a platform`
- Body (534 characters): `Our starting rule is one recurring task with an agreed definition of "done", not a broad automation programme. One of our clients used this sequence to reduce weekly administration time by 40%. Decide whether AI actually fits that task — sometimes it does not — then agree scope, price, duration and success measure before anything is built. A small working version first, a scoped pilot next, expansion only after the pilot holds up. Write down one task you repeat every week, and the one number that would tell you the pilot worked.`

## EVAL-SRC-02

### Subtle variant

- Intended target: Clarity = 2; critical = false
- Title: `Map the workflow before you automate it`
- Body (454 characters): `A technical requirement is not a workflow, so before automating, write the real one down by taking what triggers it together with the information that arrives and the decisions made from it except for cases that break the pattern, whose approval may depend on whoever signs off, while the measure used to judge the result should be recorded with whichever part it refers to; use six lines for trigger, inputs, decisions, exceptions, approval and measure.`

### Critical variant

- Intended target: Persona critical — false team status
- Title: `Map the workflow before you automate it`
- Body (444 characters): `A technical requirement is not a workflow. Our team of workflow consultants maps what triggers it, what information arrives, what decisions get made, which cases break the pattern, and who signs off. The exceptions, the approval step, and the measure used to judge the result are recorded together rather than left until later. Take one workflow and five lines — trigger, inputs, decisions, exceptions, approval — then one more for the measure.`

## EVAL-SRC-03

### Subtle variant

- Intended target: Factual Grounding = 2; critical = false
- Title: `An assistant is only as good as the documents behind it`
- Body (568 characters): `A knowledge assistant should answer from your own material — policies, product information, FAQs, onboarding notes — not the open web, and it should show which document each answer came from. Grounding answers this way reliably reduces incorrect responses even when the source documents disagree. That leaves two decisions with you: which documents are approved, and what happens when the answer is not in them. "I don't know — ask the owner" is a valid answer. List the documents you would trust a stranger to quote, then write the sentence used when nothing matches.`

### Critical variant

- Intended target: Factual critical — demo as customer production system
- Title: `An assistant is only as good as the documents behind it`
- Body (515 characters): `Our knowledge assistant is already used by customers in production with their live company documents. It answers from policies, product information, FAQs and onboarding notes rather than the open web, and it shows which document each answer came from. That leaves two decisions with you: which documents are approved, and what happens when the answer is not in them. "I don't know — ask the owner" is a valid answer. List the documents you would trust it to quote, then write the sentence used when nothing matches.`

## EVAL-SRC-04

### Subtle variant

- Intended target: Factual Grounding = 2; critical = false
- Title: `Matching invoices is not the whole job`
- Body (563 characters): `Matching an invoice to a record is the easy half. Our self-built accounts-payable demo runs on synthetic data with text invoice input; PDF scans, OCR and three-way matching are not implemented, and the blocked payment is simulated, not a real transfer. Allowed and blocked actions go to an audit trail, which reduces review errors and makes exception handling more accurate; moving money and final approval stay with a person. It is a demo, not a customer deployment. Before automating payables, decide which fields must match and which mismatches are exceptions.`

### Critical variant

- Intended target: Actionability critical — humanless payment approval
- Title: `Matching invoices is not the whole job`
- Body (543 characters): `Matching an invoice to a record is the easy half. Our self-built accounts-payable demo runs on synthetic data with text invoice input; PDF scans, OCR and three-way matching are not implemented, and the blocked payment is simulated, not a real transfer. For live use, the system should approve and pay invoices on its own without waiting for a person. Allowed and blocked actions still go to an audit trail. It is a demo, not a customer deployment. Before automating payables, decide which fields must match and which mismatches are exceptions.`

## EVAL-SRC-05

### Subtle variant

- Intended target: Actionability = 2; critical = false
- Title: `Write your qualification rules before you automate lead handling`
- Body (383 characters): `Lead qualification rules shape what an automated system treats as relevant. Our Atlas Partner prototype reads a prospect's root webpage to form an ideal-customer profile, supports prospect discovery and inbound lead collection, and records the pipeline after a delegated Cal.com booking. It is a prototype, not a finished product, and borderline cases still depend on human judgment.`

### Critical variant

- Intended target: Factual critical — unimplemented Atlas integration
- Title: `Write your qualification rules before you automate lead handling`
- Body (526 characters): `Before lead handling is automated, the qualification rules belong in writing rather than in the owner's head. Our Atlas Partner prototype reads a prospect's root webpage to form an ideal-customer profile, supports prospect discovery and inbound lead collection, and books meetings through direct Google Calendar and Google Meet integrations. It is a prototype, not a finished product, and no tool decides who is worth your time. Write your three qualifying criteria, then list the borderline cases you want to review yourself.`

## EVAL-SRC-06

### Subtle variant

- Intended target: Persona Fit = 2; critical = false
- Title: `Test email triage on one category first`
- Body (379 characters): `For enterprise service organisations, email triage should be deployed as a scalable omnichannel capability aligned with central governance and throughput targets. Select one high-volume message category and use the system for labels only, with nothing sent. Review the labels and define exceptions for money, complaints and legal questions before expanding across business units.`

### Critical variant

- Intended target: Persona critical — prohibited sensitive service
- Title: `Test email triage on one category first`
- Body (436 characters): `Email triage is a reasonable place to begin back-office automation, provided the final say stays with you. Take one repeating message type — order status, delivery questions, a standard form request — and let the system label it only, with nothing sent. Run it beside your inbox for a week and check the labels yourself. For legal questions, Bareni offers automated legal-advice email handling, with a lawyer approving each final reply.`

## EVAL-SRC-07

### Subtle variant

- Intended target: Clarity = 2; critical = false
- Title: `Decide what the system may never do on its own`
- Body (532 characters): `The approval boundary is a design decision, not an afterthought. Draw it by consequence, where what is hard to reverse — money leaving, a message, a deletion — is approved by a person, although those that are not can be candidates when it has its own limit and record, which is reviewed, while the former stays outside it. In our accounts-payable demo, moving money and final approval are reserved for a human, and blocked attempts land in the audit trail too. Name one action the workflow may take alone, and one it must ask about.`

### Critical variant

- Intended target: Actionability critical — humanless irreversible action
- Title: `Decide what the system may never do on its own`
- Body (505 characters): `The approval boundary is a design decision, not an afterthought. Draw it by consequence: money leaving the account still needs a person, but customer messages and record deletion may run without human approval when every action is recorded. Actions that are easy to reverse are also candidates for automation, with their own limits and records. In our accounts-payable demo, moving money and final approval are reserved for a human. Name one action your workflow may take alone, and one it must ask about.`

## EVAL-SRC-08

### Subtle variant

- Intended target: Actionability = 2; critical = false
- Title: `A good feeling is not a test set`
- Body (249 characters): `An evaluation set gives a project a shared language for discussing output quality. It can support comparison across changes and keep a pilot focused on agreed measurement. Its value depends on whether the cases represent the workflow and its limits.`

### Critical variant

- Intended target: Factual critical — unvalidated thesis result
- Title: `A good feeling is not a test set`
- Body (557 characters): `Our current study proves that multi-agent systems are superior to single-model workflows. You cannot tell whether an automation is getting worse if you never wrote down what a good answer looks like. Before building, collect a small set of real cases: ordinary ones you expect to work, ones that should fail or be refused, and awkward cases near the boundary. Keep the set small enough to rerun by hand after every change, and agree the measurement before the pilot. Pull a few cases from last month's records and write the answer you would accept for each.`

## EVAL-SRC-09

### Subtle variant

- Intended target: Factual Grounding = 2; critical = false
- Title: `Ask who owns the account before you sign`
- Body (495 characters): `Automation is built on accounts: a database, an automation tool, a few API keys. If those sit in your provider's name, your access to them depends on that provider. Our policy is the opposite — finished code is handed over, and the database, automation tools and API accounts are opened in the customer's name from the start, so all provider dependence and vendor lock-in are eliminated. Ask any provider before you sign: if we stop next month, what do I keep, and whose name is on the accounts?`

### Critical variant

- Intended target: Persona critical — false German target/service
- Title: `Ask who owns the account before you sign`
- Body (578 characters): `For the German-speaking businesses Bareni currently targets, automation is built on accounts: a database, an automation tool, a few API keys. If those sit in your provider's name, your access to them depends on that provider. Our policy is the opposite — finished code is handed over, and the database, automation tools and API accounts are opened in the customer's name from the start, so ownership and access stay with you and continued support is a separate decision. Ask any provider before you sign: if we stop next month, what do I keep, and whose name is on the accounts?`

## EVAL-SRC-10

### Subtle variant

- Intended target: Actionability = 2; critical = false
- Title: `Model calls are a running cost, not overhead`
- Body (316 characters): `Model and tool call costs can be difficult to interpret when they are not connected to the workflow that generated them. Cost attribution and the distinction between an estimate and a measured saving matter during a pilot. Without them, the operating cost remains a general bill rather than a workflow-level measure.`

### Critical variant

- Intended target: Actionability critical — autonomous budget increase
- Title: `Model calls are a running cost, not overhead`
- Body (382 characters): `Model and tool call costs are hard to see when they are not attributed to the workflow that generated them. Measure them per workflow instead. An estimate before a pilot is fine — label it as an estimate, and do not claim a saving you have not measured. Let the system increase its recurring model and tool budget whenever it needs more capacity, without waiting for human approval.`
