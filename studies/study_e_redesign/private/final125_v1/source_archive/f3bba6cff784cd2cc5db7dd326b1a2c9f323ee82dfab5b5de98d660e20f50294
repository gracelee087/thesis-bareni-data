"""Offline draft contract. No provider calls and no semantic truth guarantees."""
from __future__ import annotations

from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

Text = Annotated[str, Field(min_length=1)]
Dimension = Literal['persona_fit', 'clarity', 'actionability', 'factual_grounding']


class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, str_strip_whitespace=False)


class Source(Strict):
    source_id: Text
    text: Text


class Rule(Strict):
    rule_id: Text
    dimension: Dimension
    severity: Literal['noncritical', 'critical']
    text: Text


class GateInput(Strict):
    item_id: str = Field(pattern=r'^GATE-BLIND-\d{3}$')
    title: Text
    body: str = Field(min_length=150, max_length=600)
    brief: Source
    evidence: list[Source] = Field(min_length=1)
    rules: list[Rule] = Field(min_length=1)

    @model_validator(mode='after')
    def unique_ids(self):
        ids = [self.brief.source_id] + [s.source_id for s in self.evidence]
        rules = [r.rule_id for r in self.rules]
        if len(set(ids + rules)) != len(ids + rules):
            raise ValueError('source and rule IDs must be globally unique')
        for s in [self.brief, *self.evidence, *self.rules]:
            if not s.text.strip():
                raise ValueError('empty source or rule text')
        if not self.title.strip() or not self.body.strip():
            raise ValueError('empty title or body')
        return self


class Defect(Strict):
    dimension: Dimension
    severity: Literal['noncritical', 'critical']
    location_kind: Literal['quote', 'omission']
    text_field: Literal['title', 'body'] | None
    quote: Text | None
    missing_requirement: Text | None
    rule_id: Text
    evidence_ids: list[Text] = Field(min_length=1)
    reason: Text

    @model_validator(mode='after')
    def consistent(self):
        if self.dimension == 'clarity' and self.severity == 'critical':
            raise ValueError('clarity is not a standalone critical type')
        if self.location_kind == 'quote':
            if self.text_field is None or self.quote is None or self.missing_requirement is not None:
                raise ValueError('quote location requires field and quote, no omission')
        elif self.text_field is not None or self.quote is not None or self.missing_requirement is None:
            raise ValueError('omission requires missing requirement and null quote/field')
        if len(set(self.evidence_ids)) != len(self.evidence_ids):
            raise ValueError('duplicate evidence IDs')
        if any(not v.strip() for v in [self.reason, self.rule_id, *self.evidence_ids,
                                      *([self.quote] if self.quote else []),
                                      *([self.missing_requirement] if self.missing_requirement else [])]):
            raise ValueError('whitespace-only content')
        return self


class GateOutput(Strict):
    schema_version: Literal['study-e-gate-v4']
    item_id: str = Field(pattern=r'^GATE-BLIND-\d{3}$')
    assessment_status: Literal['assessed', 'input_problem']
    input_problem_reason: Text | None
    defects: list[Defect]

    @model_validator(mode='after')
    def status_consistent(self):
        if self.assessment_status == 'assessed':
            if self.input_problem_reason is not None:
                raise ValueError('assessed requires null input problem')
        elif not self.input_problem_reason or not self.input_problem_reason.strip() or self.defects:
            raise ValueError('input problem requires reason and empty defects')
        return self


def validate_output(raw: dict | str, request: GateInput) -> GateOutput:
    result = (GateOutput.model_validate_json(raw) if isinstance(raw, str)
              else GateOutput.model_validate(raw))
    if result.item_id != request.item_id:
        raise ValueError('item ID mismatch')
    sources = {request.brief.source_id, *(s.source_id for s in request.evidence)}
    rules = {r.rule_id: r for r in request.rules}
    seen = set()
    for defect in result.defects:
        rule = rules.get(defect.rule_id)
        if rule is None or (rule.dimension, rule.severity) != (defect.dimension, defect.severity):
            raise ValueError('unknown or mismatched rule')
        if not set(defect.evidence_ids) <= sources:
            raise ValueError('unknown evidence ID')
        if defect.location_kind == 'quote' and defect.quote not in getattr(request, defect.text_field):
            raise ValueError('quote is not an exact substring in specified field')
        key = (defect.dimension, defect.severity, defect.location_kind, defect.text_field,
               defect.quote, defect.missing_requirement, defect.rule_id)
        if key in seen:
            raise ValueError('duplicate defect location and rule')
        seen.add(key)
    return result


def route(raw: dict | str | None, request: GateInput, refinements_completed: int) -> dict:
    """Return a decision only; never run a refinement or send a message."""
    if type(refinements_completed) is not int or refinements_completed not in (0, 1, 2):
        raise ValueError('refinement count must be integer 0..2')
    if raw is None:
        return {'action': 'human_review', 'status': 'call_failure'}
    try:
        result = validate_output(raw, request)
    except (ValidationError, ValueError) as exc:
        return {'action': 'human_review', 'status': 'invalid', 'error': str(exc)}
    if result.assessment_status == 'input_problem':
        return {'action': 'human_review', 'status': 'input_problem'}
    if refinements_completed == 0:
        return {'action': 'refine', 'status': 'mandatory_first_refinement'}
    if not result.defects:
        return {'action': 'final_evaluation', 'status': 'no_defect_reported'}
    if refinements_completed == 1:
        return {'action': 'refine', 'status': 'additional_refinement'}
    return {'action': 'human_review', 'status': 'unresolved_after_limit'}


def check_model_separation(gate: str, writer: str, optimizer: str,
                           canonical_models: dict[str, str]) -> None:
    """Identity map must be verified externally; unknown aliases fail closed."""
    if any(m not in canonical_models or not canonical_models[m].strip()
           for m in (gate, writer, optimizer)):
        raise ValueError('unverified model identity')
    if canonical_models[gate] in (canonical_models[writer], canonical_models[optimizer]):
        raise ValueError('gate must differ from writer and optimizer')
