from pydantic import BaseModel, ConfigDict
from typing import List

class RiskLedgerRead(BaseModel):
    id: str
    risk_type: str
    severity_level: str
    financial_exposure: float
    recommendation: str

    # هذا السطر السحري يمنع خطأ 500 الصامت ويسمح بقراءة قاعدة البيانات
    model_config = ConfigDict(from_attributes=True)

class SimulationRead(BaseModel):
    scenario_name: str
    simulated_loss: float
    win_probability: float
    lc_score_impact: float

class RiskDashboardResponse(BaseModel):
    total_exposure: float
    risk_breakdown: List[RiskLedgerRead]
    executive_summary: str
    mitigation_actions: List[str]
    win_probability: float

class SimulationRequest(BaseModel):
    reduce_imports_pct: float = 0.0
    restructure_payroll_pct: float = 0.0