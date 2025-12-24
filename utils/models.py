from typing import Any, Dict, List, Literal
from pydantic import BaseModel, field_validator, TypeAdapter


# ================================
# Flat models for domain risk analysis (base risks)
# ================================
class RiskItem(BaseModel):
    """
    Represents a risk item in the domain analysis.

    Attributes:
        title (str): The title of the risk.
        explanation (str): Explanation of the risk.
        severity (Literal["low", "medium", "high"]): Severity level of the risk.
        mitigation (str): Suggested mitigation for the risk.
    """

    title: str
    explanation: str
    severity: Literal["low", "medium", "high"]
    mitigation: str

    @field_validator("title", "explanation", "severity", "mitigation", mode="before")
    def _non_empty(cls, v: str) -> str:
        if not isinstance(v, str) or not v.strip():
            raise ValueError("Il campo non può essere vuoto")
        return v


class DomainItem(BaseModel):
    """
    Represents a domain item containing a list of risks.

    Attributes:
        risks (List[RiskItem]): A list of risk items associated with the domain.
    """

    risks: List[RiskItem]


DomainAnalysisAdapter = TypeAdapter(Dict[str, DomainItem])


# ================================
# Flat models for Gemini validation (causality extends base risk)
# ================================
class CausalityItem(RiskItem):
    """
    Represents a causality item extending the base risk item with additional fields.

    Attributes:
        severity_rationale (str): Rationale for the severity.
        entity (Literal["ai", "human", "other"]): The entity involved.
        entity_rationale (str): Rationale for the entity.
        intent (Literal["intentional", "unintentional", "other"]): The intent.
        intent_rationale (str): Rationale for the intent.
        timing (Literal["pre-deployment", "post-deployment", "other"]): The timing.
        timing_rationale (str): Rationale for the timing.
    """

    severity_rationale: str
    entity: Literal["ai", "human", "other"]
    entity_rationale: str
    intent: Literal["intentional", "unintentional", "other"]
    intent_rationale: str
    timing: Literal["pre-deployment", "post-deployment", "other"]
    timing_rationale: str

    @field_validator(
        "severity_rationale",
        "entity_rationale",
        "intent_rationale",
        "timing_rationale",
        mode="before",
    )
    def _non_empty_causality(cls, v: str) -> str:
        if not isinstance(v, str) or not v.strip():
            raise ValueError("Il campo non può essere vuoto")
        return v


class CausalityDomainItem(BaseModel):
    """
    Represents a causality domain item containing a list of causality risks.

    Attributes:
        risks (List[CausalityItem]): A list of causality items associated with the domain.
    """

    risks: List[CausalityItem]


CausalityAdapter = TypeAdapter(Dict[str, CausalityDomainItem])


# ================================
# Nested models for final output with causality block
# ================================
class EntityField(BaseModel):
    """
    Represents the entity field with its value and rationale.

    Attributes:
        value (Literal["ai", "human", "other"]): The entity involved.
        rationale (str): Rationale for the entity.
    """

    value: Literal["ai", "human", "other"]
    rationale: str

    @field_validator("rationale", mode="before")
    def _non_empty(cls, v: str) -> str:
        if not isinstance(v, str) or not v.strip():
            raise ValueError("La motivazione entity non può essere vuota")
        return v


class IntentField(BaseModel):
    """
    Represents the intent field with its value and rationale.

    Attributes:
        value (Literal["intentional", "unintentional", "other"]): The intent.
        rationale (str): Rationale for the intent.
    """

    value: Literal["intentional", "unintentional", "other"]
    rationale: str

    @field_validator("rationale", mode="before")
    def _non_empty(cls, v: str) -> str:
        if not isinstance(v, str) or not v.strip():
            raise ValueError("La motivazione intent non può essere vuota")
        return v


class TimingField(BaseModel):
    """
    Represents the timing field with its value and rationale.

    Attributes:
        value (Literal["pre-deployment", "post-deployment", "other"]): The timing.
        rationale (str): Rationale for the timing.
    """

    value: Literal["pre-deployment", "post-deployment", "other"]
    rationale: str

    @field_validator("rationale", mode="before")
    def _non_empty(cls, v: str) -> str:
        if not isinstance(v, str) or not v.strip():
            raise ValueError("La motivazione timing non può essere vuota")
        return v


class CausalityBlock(BaseModel):
    """
    Represents the causality block containing entity, intent, and timing fields.

    Attributes:
        entity (EntityField): The entity field.
        intent (IntentField): The intent field.
        timing (TimingField): The timing field.
    """

    entity: EntityField
    intent: IntentField
    timing: TimingField


class RiskItemNested(BaseModel):
    """
    Represents a risk item with nested causality block.

    Attributes:
        title (str): The title of the risk.
        explanation (str): Explanation of the risk.
        severity (Literal["low", "medium", "high"]): Severity level of the risk.
        severity_rationale (str): Rationale for the severity.
        mitigation (str): Mitigation measures for the risk.
    """

    title: str
    explanation: str
    severity: Literal["low", "medium", "high"]
    severity_rationale: str
    mitigation: str
    causality: CausalityBlock

    @field_validator(
        "title", "explanation", "severity_rationale", "mitigation", mode="before"
    )
    def _non_empty(cls, v: str) -> str:
        if not isinstance(v, str) or not v.strip():
            raise ValueError("Il campo non può essere vuoto")
        return v


class CausalityDomainItemNested(BaseModel):
    """
    Represents a causality domain item containing a list of nested risk items.

    Attributes:
        risks (List[RiskItemNested]): A list of nested risk items associated with the domain.
    """

    risks: List[RiskItemNested]
