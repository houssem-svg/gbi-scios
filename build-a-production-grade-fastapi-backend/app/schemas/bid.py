"""Pydantic schemas for the Bid model."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from app.models.bid import EvaluationFormula


class BidBase(BaseModel):
    supplier_id: UUID
    submitted_price: Decimal = Field(..., ge=0)
    local_content_score: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    evaluation_formula: EvaluationFormula = EvaluationFormula.SIXTY_FORTY
    custom_lc_weight: Decimal | None = Field(default=None, ge=0, le=100)
    custom_price_weight: Decimal | None = Field(default=None, ge=0, le=100)
    # Optional pharma discount rate (0.0–1.0). Applied to submitted_price
    # BEFORE the SME preference per the engineering spec (💡.docx line 812-813):
    #   P_adjusted = P_eval × (1 - PharmaDiscountRate)
    pharma_discount_rate: Decimal = Field(default=Decimal("0"), ge=0, le=1)


class BidCreate(BidBase):
    pass


class BidRead(BidBase):
    id: UUID
    project_id: UUID
    sme_preference_applied: bool
    tadawul_bonus_applied: bool
    pharma_discount_applied: bool
    effective_price: Decimal | None
    final_score: Decimal | None
    rank: int | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer(
        "submitted_price",
        "local_content_score",
        "custom_lc_weight",
        "custom_price_weight",
        "pharma_discount_rate",
        "effective_price",
        "final_score",
    )
    def serialize_decimal(self, value: Decimal | None) -> float | None:
        return float(value) if value is not None else None

    @field_serializer("id", "project_id", "supplier_id")
    def serialize_uuid(self, value: UUID) -> str:
        return str(value)
