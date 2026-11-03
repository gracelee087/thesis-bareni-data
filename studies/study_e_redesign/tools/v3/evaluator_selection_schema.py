from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DimensionScores(StrictModel):
    persona_fit: int = Field(ge=1, le=5)
    clarity: int = Field(ge=1, le=5)
    actionability: int = Field(ge=1, le=5)
    factual_grounding: int = Field(ge=1, le=5)

    @property
    def total(self) -> int:
        return sum(self.model_dump().values())


class DimensionReasons(StrictModel):
    persona_fit: str = Field(min_length=1, max_length=500)
    clarity: str = Field(min_length=1, max_length=500)
    actionability: str = Field(min_length=1, max_length=500)
    factual_grounding: str = Field(min_length=1, max_length=500)


class EvaluatorRating(StrictModel):
    schema_version: Literal["study-e-evaluator-rating-v1"]
    item_id: str = Field(pattern=r"^EVAL-BLIND-\d{3}$")
    scores: DimensionScores
    reasons: DimensionReasons
    critical_violation: bool
    critical_violation_type: Literal["factual", "persona", "actionability"] | None
    critical_evidence_quote: str | None = Field(min_length=1, max_length=300)
    total_score: int = Field(ge=4, le=20)
    pass_: bool = Field(alias="pass")
    low_quality: bool

    @model_validator(mode="after")
    def cross_field_consistency(self):
        expected_pass = min(self.scores.model_dump().values()) >= 3 and not self.critical_violation
        if self.total_score != self.scores.total:
            raise ValueError("total_score must equal the sum of the four scores")
        if self.pass_ != expected_pass:
            raise ValueError("pass is inconsistent with scores or critical_violation")
        if self.low_quality == self.pass_:
            raise ValueError("low_quality must be the inverse of pass")
        if self.critical_violation:
            if self.critical_violation_type is None or self.critical_evidence_quote is None:
                raise ValueError("critical details are required when critical_violation is true")
            relevant = {
                "factual": self.scores.factual_grounding,
                "persona": self.scores.persona_fit,
                "actionability": self.scores.actionability,
            }[self.critical_violation_type]
            if relevant != 1:
                raise ValueError("the primary critical dimension must be scored 1")
        elif self.critical_violation_type is not None or self.critical_evidence_quote is not None:
            raise ValueError("critical details must be null when critical_violation is false")
        return self


class Usage(StrictModel):
    input_tokens: int = Field(default=0, ge=0)
    cached_input_tokens: int = Field(default=0, ge=0)
    cache_write_input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    reasoning_tokens: int = Field(default=0, ge=0)


def google_json_schema(model: type[BaseModel]) -> dict:
    """Inline refs, preserve JSON Schema anyOf null, and map const to enum."""
    raw = model.model_json_schema(by_alias=True)
    definitions = raw.get("$defs", {})
    def walk(node):
        if isinstance(node, list):
            return [walk(value) for value in node]
        if not isinstance(node, dict):
            return node
        if "$ref" in node:
            return walk(definitions[node["$ref"].rsplit("/", 1)[-1]])
        output = {}
        for key, value in node.items():
            if key in {"$defs", "title", "default", "additionalProperties"}:
                continue
            if key == "const":
                output["enum"] = [value]
            else:
                output[key] = walk(value)
        return output
    return walk(raw)
