# app/schemas/dashboard.py

from pydantic import BaseModel
from typing import List, Dict, Any

class ComplianceBreakdown(BaseModel):
    open_flags: int
    resolved_flags: int
    waived_flags: int
    total_flags: int

class TopRiskProject(BaseModel):
    project_id: str
    project_name: str
    total_exposure: float
    unresolved_flags: int

class DashboardSummaryResponse(BaseModel):
    total_projects: int
    total_budget_managed: float
    total_financial_exposure: float
    overall_compliance_score: float
    compliance_breakdown: ComplianceBreakdown
    top_risk_projects: List[TopRiskProject]