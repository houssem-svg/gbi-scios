"""Pydantic schemas for evaluation criteria + results."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from app.models.bid import EvaluationFormula


class EvaluationCriteriaBase(BaseModel):
    formula: EvaluationFormula = EvaluationFormula.SIXTY_FORTY
    lc_weight: Decimal = Field(default=Decimal("60.00"), ge=0, le=100)
    price_weight: Decimal = Field(default=Decimal("40.00"), ge=0, le=100)
    sme_preference_pct: Decimal = Field(default=Decimal("10.00"), ge=0, le=100)
    tadawul_bonus_pts: Decimal = Field(default=Decimal("5.00"), ge=0, le=100)
    rhq_required: bool = False
    risk_cap_pct: Decimal = Field(default=Decimal("25.00"), ge=0, le=100)
    waiver_cap_pct: Decimal = Field(default=Decimal("10.00"), ge=0, le=100)


class EvaluationCriteriaCreate(EvaluationCriteriaBase):
    pass


class EvaluationCriteriaUpdate(BaseModel):
    formula: EvaluationFormula | None = None
    lc_weight: Decimal | None = Field(default=None, ge=0, le=100)
    price_weight: Decimal | None = Field(default=None, ge=0, le=100)
    sme_preference_pct: Decimal | None = Field(default=None, ge=0, le=100)
    tadawul_bonus_pts: Decimal | None = Field(default=None, ge=0, le=100)
    rhq_required: bool | None = None
    risk_cap_pct: Decimal | None = Field(default=None, ge=0, le=100)
    waiver_cap_pct: Decimal | None = Field(default=None, ge=0, le=100)


class EvaluationCriteriaRead(EvaluationCriteriaBase):
    id: UUID
    project_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer(
        "lc_weight",
        "price_weight",
        "sme_preference_pct",
        "tadawul_bonus_pts",
        "risk_cap_pct",
        "waiver_cap_pct",
    )
    def serialize_decimal(self, value: Decimal) -> float:
        return float(value)

    @field_serializer("id", "project_id")
    def serialize_uuid(self, value: UUID) -> str:
        return str(value)


class EvaluationResultRead(BaseModel):
    id: UUID
    project_id: UUID
    bid_id: UUID
    effective_price: Decimal
    final_score: Decimal
    rank: int
    disqualified: bool
    disqualification_reason: str | None
    breakdown_json: str
    calculated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("effective_price", "final_score")
    def serialize_decimal(self, value: Decimal) -> float:
        return float(value)

    @field_serializer("id", "project_id", "bid_id")
    def serialize_uuid(self, value: UUID) -> str:
        return str(value)


class EvaluationRunResponse(BaseModel):
    project_id: UUID
    results: list[EvaluationResultRead]
    risk_cap_breached: bool
    risk_cap_pct: Decimal
    total_exposure: Decimal
    project_budget: Decimal

    @field_serializer("risk_cap_pct", "total_exposure", "project_budget")
    def serialize_decimal(self, value: Decimal) -> float:
        return float(value)

    @field_serializer("project_id")
    def serialize_uuid(self, value: UUID) -> str:
        return str(value)
