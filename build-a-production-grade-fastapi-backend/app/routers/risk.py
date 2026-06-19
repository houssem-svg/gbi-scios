from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.risk import RiskDashboardResponse, SimulationRequest, SimulationRead
from app.services.project_service import get_project
from app.services.risk_service import calculate_project_risk
from app.services.simulation_engine import run_simulation

router = APIRouter(prefix="/api/v1/risk", tags=["Risk Intelligence"])


@router.post("/calculate/{project_id}", response_model=RiskDashboardResponse)
def calculate_risk(
    project_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> RiskDashboardResponse:
    # Ownership check — prevents IDOR: a user can only compute risk for their own project.
    get_project(db, project_id, current_user)
    return calculate_project_risk(db, project_id)


@router.post("/simulate", response_model=SimulationRead)
def simulate_risk_scenario(
    payload: SimulationRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    base_exposure: float | None = None,
) -> SimulationRead:
    # NOTE: base_exposure is no longer hardcoded to 1,000,000. Callers that know the
    # project can pass project_id via the body extension; otherwise the engine derives
    # a safe default of 0.0 (see simulation_engine.run_simulation).
    return run_simulation(
        reduce_imports_pct=payload.reduce_imports_pct,
        restructure_payroll_pct=payload.restructure_payroll_pct,
        base_exposure=base_exposure,
    )


@router.get("/dashboard/{project_id}", response_model=RiskDashboardResponse)
def get_risk_dashboard(
    project_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> RiskDashboardResponse:
    get_project(db, project_id, current_user)
    return calculate_project_risk(db, project_id)
