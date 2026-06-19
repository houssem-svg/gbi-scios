"""Payroll router — exposes LCP payroll leakage calculations.

Routes (all require ``get_current_user`` and enforce project ownership):

- POST  /api/v1/payroll/{project_id}           → PayrollLedgerRead (create a ledger)
- GET   /api/v1/payroll/{project_id}           → list[PayrollLedgerRead]
- GET   /api/v1/payroll/{project_id}/leakage   → PayrollLeakageResult
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.payroll import (
    PayrollLedgerCreate,
    PayrollLedgerRead,
    PayrollLeakageResult,
)
from app.services.payroll_service import (
    calculate_payroll_leakage,
    create_payroll_ledger,
    list_project_payroll_ledgers,
)

router = APIRouter(prefix="/api/v1/payroll", tags=["Payroll & LCP Leakage"])


@router.post(
    "/{project_id}",
    response_model=PayrollLedgerRead,
    status_code=status.HTTP_201_CREATED,
)
def create_ledger(
    project_id: UUID,
    payload: PayrollLedgerCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> PayrollLedgerRead:
    return PayrollLedgerRead.model_validate(
        create_payroll_ledger(db, project_id, payload, current_user)
    )


@router.get("/{project_id}", response_model=list[PayrollLedgerRead])
def list_ledgers(
    project_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[PayrollLedgerRead]:
    ledgers = list_project_payroll_ledgers(db, project_id, current_user)
    return [PayrollLedgerRead.model_validate(l) for l in ledgers]


@router.get("/{project_id}/leakage", response_model=PayrollLeakageResult)
def get_leakage(
    project_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> PayrollLeakageResult:
    """Compute the LCP payroll leakage for the project.

    Returns the Saudi payroll recognized (53.4%), Saudi payroll leakage (46.6%),
    expat payroll leakage (100%), and total leakage.
    """
    return calculate_payroll_leakage(db, project_id, current_user)
