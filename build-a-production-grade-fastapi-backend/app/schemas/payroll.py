"""Pydantic schemas for the PayrollLedger model."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_serializer


class PayrollLedgerBase(BaseModel):
    total_budget: Decimal = Field(..., ge=0)
    saudi_payroll: Decimal = Field(..., ge=0)
    expat_payroll: Decimal = Field(..., ge=0)
    period_start: date
    period_end: date


class PayrollLedgerCreate(PayrollLedgerBase):
    pass


class PayrollLedgerRead(PayrollLedgerBase):
    id: UUID
    project_id: UUID
    source_file_id: UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("total_budget", "saudi_payroll", "expat_payroll")
    def serialize_decimal(self, value: Decimal) -> float:
        return float(value)

    @field_serializer("id", "project_id", "source_file_id")
    def serialize_uuid(self, value: UUID | None) -> str | None:
        return str(value) if value is not None else None


class PayrollLeakageResult(BaseModel):
    """Result of computing LCP payroll leakage for a project."""

    project_id: UUID
    saudi_payroll_total: float
    expat_payroll_total: float
    # 53.4% of Saudi payroll is recognized as local content.
    saudi_payroll_recognized: float
    # 46.6% of Saudi payroll is leakage (1 - 0.534).
    saudi_payroll_leakage: float
    # All expat payroll is leakage (value leaving the Kingdom).
    expat_payroll_leakage: float
    total_payroll_leakage: float
    recognition_factor: float

    @field_serializer("project_id")
    def serialize_uuid(self, value: UUID) -> str:
        return str(value)
