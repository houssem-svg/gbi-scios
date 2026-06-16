# app/schemas/reporting.py

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_serializer

from app.models.reporting import ReportStatus, ReportType

# --- المخططات التفصيلية للبيانات المجمعة ---

class ComplianceSummarySchema(BaseModel):
    total_violations: int
    resolved_violations: int
    unresolved_violations: int
    total_non_compliant_value: float
    top_violation_categories: List[Dict[str, Any]]

class ExposureMetricsSchema(BaseModel):
    total_financial_exposure: float
    mandatory_list_penalties: float
    estimated_payroll_leakage: float
    exposure_percentage_vs_project_budget: float

class RiskProfileSchema(BaseModel):
    risk_level: str  # LOW / MODERATE / HIGH / CRITICAL
    critical_flags_count: int
    top_risk_items: List[Dict[str, Any]]
    executive_risk_summary: str

class AggregatedPayloadSchema(BaseModel):
    metadata: Dict[str, Any]
    compliance_summary: ComplianceSummarySchema
    exposure_metrics: ExposureMetricsSchema
    risk_profile: RiskProfileSchema

# --- مخططات الطلب والاستجابة الأساسية ---

class ReportGenerateRequest(BaseModel):
    project_id: str  
    report_type: ReportType = ReportType.EXECUTIVE

class ReportRead(BaseModel):
    id: int
    project_id: UUID
    generated_by: Optional[UUID]
    report_type: ReportType
    status: ReportStatus
    json_payload: Optional[AggregatedPayloadSchema]  # التحقق من الهيكل المجمع الجديد
    file_path: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("project_id", "generated_by")
    def serialize_uuid(self, value: UUID | None) -> str | None:
        return str(value) if value is not None else None

class ReportListResponse(BaseModel):
    data: list[ReportRead]
    total: int
