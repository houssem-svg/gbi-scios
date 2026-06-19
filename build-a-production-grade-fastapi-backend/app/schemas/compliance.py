from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.compliance import ComplianceFlagStatus, ViolationType
from app.models.mandatory_list import MandatoryStatus


class MandatoryListUploadResult(BaseModel):
    imported_rows: int
    failed_rows: int
    validation_errors: list[str]


class MandatoryListItemRead(BaseModel):
    id: UUID
    item_code: str
    product_name: str
    category: str
    local_manufacturer: str
    mandatory_status: MandatoryStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ComplianceFlagRead(BaseModel):
    id: UUID
    project_id: UUID
    boq_item_id: UUID
    mandatory_item_id: UUID
    violation_type: ViolationType
    penalty_percentage: Decimal
    exposure_amount: Decimal
    status: ComplianceFlagStatus
    created_at: datetime
    updated_at: datetime | None = None
    waived_by: UUID | None = None
    waived_at: datetime | None = None
    waiver_reason: str | None = None
    waiver_strategy_id: UUID | None = None
    boq_item_code: str | None = None
    boq_description: str | None = None
    mandatory_product_name: str | None = None

    model_config = ConfigDict(from_attributes=True)


class FlagStatusUpdate(BaseModel):
    """Request body for PATCH /compliance/flags/{flag_id}.

    Use this to waive or resolve a compliance flag. Only Admin/Consultant
    (compliance officer) roles may call it. A waiver_reason is mandatory.
    Optionally link a generated WaiverStrategy id and cap the waived amount
    (the service enforces the project's waiver cap percentage).
    """
    status: ComplianceFlagStatus
    waiver_reason: str = Field(min_length=3, max_length=1000)
    waiver_strategy_id: UUID | None = None


class ComplianceScanResult(BaseModel):
    total_scanned_items: int
    matched_violations: int
    total_exposure: Decimal
    compliance_status: str
    flags: list[ComplianceFlagRead]
