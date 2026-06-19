"""Payroll service — LCP payroll leakage calculation.

Per the engineering spec (💡.docx Microservice 2, line 874 + JSON example
line 1315-1323):

    Exposure = Penalty_ML + PayrollLeakage + SubcontractorLeakage

The payroll leakage is the portion of payroll NOT recognized as local
content. Per the Local Content Program (LCP) methodology:

    SaudiPayrollRecognized = SaudiPayroll × 0.534   (53.4% recognized)
    SaudiPayrollLeakage    = SaudiPayroll × 0.466   (46.6% leakage)
    ExpatPayrollLeakage    = ExpatPayroll           (100% leakage)

    TotalPayrollLeakage = SaudiPayrollLeakage + ExpatPayrollLeakage

The 0.534 factor is configurable via ``settings.saudi_payroll_recognition_factor``.
"""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.payroll import PayrollLedger
from app.models.user import User
from app.schemas.payroll import PayrollLeakageResult, PayrollLedgerCreate, PayrollLedgerRead
from app.services.project_service import get_project


def create_payroll_ledger(
    db: Session,
    project_id: UUID,
    payload: PayrollLedgerCreate,
    current_user: User,
) -> PayrollLedger:
    get_project(db, project_id, current_user)
    ledger = PayrollLedger(
        project_id=project_id,
        total_budget=payload.total_budget,
        saudi_payroll=payload.saudi_payroll,
        expat_payroll=payload.expat_payroll,
        period_start=payload.period_start,
        period_end=payload.period_end,
    )
    db.add(ledger)
    db.commit()
    db.refresh(ledger)
    return ledger


def list_project_payroll_ledgers(
    db: Session,
    project_id: UUID,
    current_user: User,
) -> list[PayrollLedger]:
    get_project(db, project_id, current_user)
    stmt = (
        select(PayrollLedger)
        .where(PayrollLedger.project_id == project_id)
        .order_by(PayrollLedger.period_end.desc())
    )
    return list(db.scalars(stmt).all())


def calculate_payroll_leakage(
    db: Session,
    project_id: UUID,
    current_user: User,
) -> PayrollLeakageResult:
    """Compute the LCP payroll leakage for a project.

    Aggregates all payroll ledgers for the project, then applies the LCP
    recognition factor (0.534) to the Saudi payroll and treats 100% of
    expat payroll as leakage.
    """
    get_project(db, project_id, current_user)
    ledgers = list_project_payroll_ledgers(db, project_id, current_user)

    saudi_total = sum((Decimal(l.saudi_payroll) for l in ledgers), Decimal("0"))
    expat_total = sum((Decimal(l.expat_payroll) for l in ledgers), Decimal("0"))

    factor = Decimal(str(settings.saudi_payroll_recognition_factor))
    leakage_factor = Decimal("1") - factor

    saudi_recognized = saudi_total * factor
    saudi_leakage = saudi_total * leakage_factor
    expat_leakage = expat_total  # 100% of expat payroll is leakage
    total_leakage = saudi_leakage + expat_leakage

    return PayrollLeakageResult(
        project_id=project_id,
        saudi_payroll_total=float(saudi_total),
        expat_payroll_total=float(expat_total),
        saudi_payroll_recognized=float(saudi_recognized),
        saudi_payroll_leakage=float(saudi_leakage),
        expat_payroll_leakage=float(expat_leakage),
        total_payroll_leakage=float(total_leakage),
        recognition_factor=float(factor),
    )
