from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Annotated
import traceback

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.risk import RiskDashboardResponse, SimulationRequest, SimulationRead
from app.services.risk_service import calculate_project_risk
from app.services.simulation_engine import run_simulation

router = APIRouter(prefix="/api/v1/risk", tags=["Risk Intelligence"])

@router.post("/calculate/{project_id}")
def calculate_risk(
    project_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    try:
        return calculate_project_risk(db, project_id)
    except Exception as e:
        # هنا نصطاد الخطأ المخفي ونجبره على الظهور في Swagger
        error_details = traceback.format_exc()
        raise HTTPException(status_code=500, detail=error_details)

@router.post("/simulate", response_model=SimulationRead)
def simulate_risk_scenario(
    payload: SimulationRequest,
    base_exposure: float = 1000000.0, # Will be fetched from DB in prod
    current_user: User = Depends(get_current_user)
):
    result = run_simulation(
        base_exposure=base_exposure,
        reduce_imports_pct=payload.reduce_imports_pct,
        restructure_payroll_pct=payload.restructure_payroll_pct
    )
    return result

@router.get("/dashboard/{project_id}", response_model=RiskDashboardResponse)
def get_risk_dashboard(
    project_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    try:
        return calculate_project_risk(db, project_id)
    except Exception as e:
        error_details = traceback.format_exc()
        raise HTTPException(status_code=500, detail=error_details)