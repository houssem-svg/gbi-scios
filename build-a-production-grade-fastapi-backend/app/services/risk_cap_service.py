"""Risk Cap service.

Computes the financial exposure cap for a project as
``risk_cap_pct``% of the project budget (sum of BoQ totals), and decides
whether the open-flag exposure breaches that cap.

Reused by ``bid_evaluation_service.run_evaluation`` so the run response
includes a single source of truth for the risk cap.
"""

import logging
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.boq_item import BoQItem
from app.models.compliance import ComplianceFlag, ComplianceFlagStatus
from app.models.evaluation import EvaluationCriteria

logger = logging.getLogger(__name__)


def _sum_open_exposure(db: Session, project_id: UUID) -> Decimal:
    total = db.scalar(
        select(func.coalesce(func.sum(ComplianceFlag.exposure_amount), Decimal("0"))).where(
            ComplianceFlag.project_id == project_id,
            ComplianceFlag.status == ComplianceFlagStatus.OPEN,
        )
    )
    if total is None:
        return Decimal("0")
    return Decimal(total)


def _project_budget(db: Session, project_id: UUID) -> Decimal:
    """Project budget is derived from the BoQ totals (the Project model has no
    budget field — see Task 2-a audit note on ``reporting._build_exposure_metrics``)."""
    total = db.scalar(
        select(func.coalesce(func.sum(BoQItem.total_price), Decimal("0"))).where(
            BoQItem.project_id == project_id
        )
    )
    if total is None:
        return Decimal("0")
    return Decimal(total)


def check_risk_cap(
    db: Session,
    project_id: UUID,
    criteria: EvaluationCriteria,
) -> tuple[bool, Decimal, Decimal]:
    """Return ``(breached, total_exposure, cap_amount)`` for the given project.

    ``breached`` is ``True`` only when the project has a positive budget AND the
    open-flag exposure exceeds ``criteria.risk_cap_pct``% of that budget.
    """
    total_exposure = _sum_open_exposure(db, project_id)
    project_budget = _project_budget(db, project_id)
    cap_amount = (criteria.risk_cap_pct / Decimal("100")) * project_budget

    if project_budget <= 0:
        breached = False
    else:
        breached = total_exposure > cap_amount

    logger.debug(
        "risk_cap_check project_id=%s exposure=%s budget=%s cap_pct=%s cap=%s breached=%s",
        project_id,
        total_exposure,
        project_budget,
        criteria.risk_cap_pct,
        cap_amount,
        breached,
    )
    return breached, total_exposure, cap_amount
