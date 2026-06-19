"""Pydantic schemas for the Supplier model."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from app.models.supplier import SupplierSizeCategory


class SupplierBase(BaseModel):
    legal_name: str = Field(..., min_length=1, max_length=255)
    commercial_registration_no: str = Field(..., min_length=1, max_length=120)
    size_category: SupplierSizeCategory = SupplierSizeCategory.LARGE
    monshaat_certificate_no: str | None = None
    monshaat_certificate_expiry: date | None = None
    is_tadawul_listed: bool = False
    tadawul_ticker: str | None = None
    is_rhq_qualified: bool = False
    rhq_license_no: str | None = None
    rhq_license_expiry: date | None = None


class SupplierCreate(SupplierBase):
    is_sme: bool | None = None  # optional override; derived from size_category by default


class SupplierUpdate(BaseModel):
    legal_name: str | None = None
    commercial_registration_no: str | None = None
    size_category: SupplierSizeCategory | None = None
    is_sme: bool | None = None
    monshaat_certificate_no: str | None = None
    monshaat_certificate_expiry: date | None = None
    is_tadawul_listed: bool | None = None
    tadawul_ticker: str | None = None
    is_rhq_qualified: bool | None = None
    rhq_license_no: str | None = None
    rhq_license_expiry: date | None = None


class SupplierRead(SupplierBase):
    id: UUID
    is_sme: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("id")
    def serialize_uuid(self, value: UUID) -> str:
        return str(value)
