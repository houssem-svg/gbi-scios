import uuid
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.compliance import ComplianceFlag, ComplianceFlagStatus
from app.models.payroll import PayrollLedger
from app.models.risk import RiskLedger
from app.services.executive_summary_service import generate_summary_and_actions


def calculate_severity(exposure: float) -> str:
    if exposure < 100_000:
        return "LOW"
    if exposure < 1_000_000:
        return "MODERATE"
    if exposure < 10_000_000:
        return "HIGH"
    return "CRITICAL"


def _compute_payroll_leakage(db: Session, project_id: uuid.UUID) -> float:
    """Compute the real LCP payroll leakage from stored PayrollLedger rows.

    Per the engineering spec (💡.docx line 874):
        Exposure = Penalty_ML + PayrollLeakage + SubcontractorLeakage

    PayrollLeakage = SaudiPayroll × (1 − recognition_factor) + ExpatPayroll
                   = SaudiPayroll × 0.466 + ExpatPayroll

    Returns 0.0 when no payroll ledgers exist for the project.
    """
    ledgers = list(
        db.scalars(
            select(PayrollLedger).where(PayrollLedger.project_id == project_id)
        ).all()
    )
    if not ledgers:
        return 0.0

    saudi_total = sum((Decimal(l.saudi_payroll) for l in ledgers), Decimal("0"))
    expat_total = sum((Decimal(l.expat_payroll) for l in ledgers), Decimal("0"))

    factor = Decimal(str(settings.saudi_payroll_recognition_factor))
    leakage_factor = Decimal("1") - factor
    saudi_leakage = saudi_total * leakage_factor
    total_leakage = saudi_leakage + expat_total
    return float(total_leakage)


def calculate_project_risk(db: Session, project_id: str | uuid.UUID):
    """Compute the financial risk profile for a project.

    Total exposure = OPEN compliance-flag exposure + LCP payroll leakage.
    Only OPEN flags count (WAIVED/RESOLVED are excluded). Payroll leakage is
    computed from real PayrollLedger rows using the LCP recognition factor
    (53.4% of Saudi payroll is recognized; 46.6% is leakage; 100% of expat
    payroll is leakage).
    """
    if isinstance(project_id, str):
        try:
            valid_project_id = uuid.UUID(project_id)
        except (TypeError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid project_id UUID format.",
            )
    else:
        valid_project_id = project_id

    # Sum exposure of OPEN flags only — waived/resolved flags must not inflate risk.
    total_exposure_decimal = db.scalar(
        select(func.sum(ComplianceFlag.exposure_amount)).where(
            ComplianceFlag.project_id == valid_project_id,
            ComplianceFlag.status == ComplianceFlagStatus.OPEN,
        )
    ) or Decimal("0")
    total_exposure = float(total_exposure_decimal)

    # LCP payroll leakage from real PayrollLedger data (0.0 if no ledgers).
    payroll_leakage = _compute_payroll_leakage(db, valid_project_id)
    total_sovereign_exposure = total_exposure + payroll_leakage

    severity = calculate_severity(total_sovereign_exposure)
    summary, actions = generate_summary_and_actions(severity, total_sovereign_exposure)

    ledger = RiskLedger(
        project_id=valid_project_id,
        risk_type="COMPLIANCE_AND_LEAKAGE",
        severity_level=severity,
        financial_exposure=total_sovereign_exposure,
        recommendation=actions[0] if actions else "Review operations",
    )
    db.add(ledger)
    db.commit()
    db.refresh(ledger)

    # win_probability is derived from severity (placeholder until a real model is wired);
    # CRITICAL exposure → low win probability, otherwise high.
    win_probability = 30.0 if severity == "CRITICAL" else 85.0

    return {
        "total_exposure": total_sovereign_exposure,
        "risk_breakdown": [ledger],
        "executive_summary": summary,
        "mitigation_actions": actions,
        "win_probability": win_probability,
        "payroll_leakage": payroll_leakage,
        "payroll_recognition_factor": settings.saudi_payroll_recognition_factor,
    }
