from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

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
    boq_item_code: str | None = None
    boq_description: str | None = None
    mandatory_product_name: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ComplianceScanResult(BaseModel):
    total_scanned_items: int
    matched_violations: int
    total_exposure: Decimal
    compliance_status: str
    flags: list[ComplianceFlagRead]
