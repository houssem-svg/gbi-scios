import uuid
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.compliance import ComplianceFlag, ComplianceFlagStatus
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


def calculate_project_risk(db: Session, project_id: str | uuid.UUID):
    """Compute the financial risk profile for a project.

    Only OPEN compliance flags count toward exposure (WAIVED/RESOLVED flags are
    excluded). Payroll leakage is computed using the LCP recognition factor
    (53.4% of Saudi payroll is recognized as local content; the remaining
    46.6% is leakage). Until a PayrollRecord model exists, payroll leakage
    is reported as 0.0 — never a fabricated 7% of exposure.
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

    # LCP payroll leakage: 46.6% of Saudi payroll is value leakage outside the Kingdom.
    # (53.4% is recognized as local content per the Local Content Program methodology.)
    # Until a PayrollRecord feed exists, this is 0.0 — NOT a fabricated 7% of exposure.
    payroll_leakage = 0.0
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
