import logging
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

logger = logging.getLogger(__name__)


def calculate_severity(exposure: float) -> str:
    if exposure < 100_000:
        return "LOW"
    if exposure < 1_000_000:
        return "MODERATE"
    if exposure < 10_000_000:
        return "HIGH"
    return "CRITICAL"


def _compute_payroll_leakage(db: Session, project_id: uuid.UUID) -> float:
    """Compute the LCP payroll leakage from stored PayrollLedger rows.

    Per the engineering spec (💡.docx line 874):
        PayrollLeakage = SaudiPayroll × (1 − recognition_factor) + ExpatPayroll
                       = SaudiPayroll × 0.466 + ExpatPayroll

    Graceful handling:
      - No PayrollLedger rows → return 0.0 (no crash).
      - Any Decimal/None field → treat as 0.0 (no crash).
      - Any unexpected exception → log + return 0.0 (never crash the caller).
    """
    try:
        ledgers = list(
            db.scalars(
                select(PayrollLedger).where(PayrollLedger.project_id == project_id)
            ).all()
        )
        if not ledgers:
            return 0.0

        saudi_total = Decimal("0")
        expat_total = Decimal("0")
        for l in ledgers:
            # Defensive: each field may be None or a non-numeric value.
            try:
                saudi_total += Decimal(str(l.saudi_payroll or 0))
            except Exception:
                logger.warning(
                    "Invalid saudi_payroll value on PayrollLedger %s: %r",
                    getattr(l, "id", "?"),
                    getattr(l, "saudi_payroll", None),
                )
            try:
                expat_total += Decimal(str(l.expat_payroll or 0))
            except Exception:
                logger.warning(
                    "Invalid expat_payroll value on PayrollLedger %s: %r",
                    getattr(l, "id", "?"),
                    getattr(l, "expat_payroll", None),
                )

        factor = Decimal(str(settings.saudi_payroll_recognition_factor))
        leakage_factor = Decimal("1") - factor
        saudi_leakage = saudi_total * leakage_factor
        total_leakage = saudi_leakage + expat_total
        return float(total_leakage)
    except Exception:
        logger.exception(
            "Unexpected error computing payroll leakage for project %s — returning 0.0",
            project_id,
        )
        return 0.0


def calculate_project_risk(db: Session, project_id: str | uuid.UUID):
    """Compute the financial risk profile for a project.

    Total exposure = OPEN compliance-flag exposure + LCP payroll leakage.
    Both components default to 0.0 when no data exists (no BoQ items,
    no compliance flags, no payroll ledgers) — the function NEVER crashes
    on empty data; it returns a valid zero-exposure LOW-severity result.
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

    # Sum exposure of OPEN flags only. Returns 0 when no flags exist.
    try:
        total_exposure_decimal = db.scalar(
            select(func.sum(ComplianceFlag.exposure_amount)).where(
                ComplianceFlag.project_id == valid_project_id,
                ComplianceFlag.status == ComplianceFlagStatus.OPEN,
            )
        ) or Decimal("0")
        total_exposure = float(total_exposure_decimal)
    except Exception:
        logger.exception(
            "Failed to query compliance exposure for project %s — defaulting to 0",
            valid_project_id,
        )
        total_exposure = 0.0

    # LCP payroll leakage — 0.0 when no payroll ledgers exist (graceful).
    payroll_leakage = _compute_payroll_leakage(db, valid_project_id)
    total_sovereign_exposure = total_exposure + payroll_leakage

    severity = calculate_severity(total_sovereign_exposure)
    summary, actions = generate_summary_and_actions(severity, total_sovereign_exposure)

    try:
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
    except Exception:
        logger.exception(
            "Failed to persist RiskLedger for project %s — returning result without ledger",
            valid_project_id,
        )
        db.rollback()
        ledger = None

    return {
        "total_exposure": total_sovereign_exposure,
        "risk_breakdown": [ledger] if ledger is not None else [],
        "executive_summary": summary,
        "mitigation_actions": actions,
        "win_probability": 30.0 if severity == "CRITICAL" else 85.0,
        "payroll_leakage": payroll_leakage,
        "payroll_recognition_factor": settings.saudi_payroll_recognition_factor,
    }
