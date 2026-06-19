"""Risk Cap service.

Per the engineering spec (💡.docx Microservice 2, line 870 + code 902-910):

    FinalPenalty = min(TotalCalculatedPenalties, P_eval × cap_rate)

The risk cap limits the total financial penalty to ``risk_cap_pct``% of the
winning bid value (``P_eval``). When the cap is breached, the *effective*
penalty is clamped to the cap amount — not merely reported as breached.

Reused by ``bid_evaluation_service.run_evaluation`` so the run response
includes a single source of truth for the risk cap.
"""

import logging
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.compliance import ComplianceFlag, ComplianceFlagStatus
from app.models.evaluation import EvaluationCriteria

logger = logging.getLogger(__name__)


def _sum_open_exposure(db: Session, project_id: UUID) -> Decimal:
    """Total exposure_amount of OPEN compliance flags for the project."""
    total = db.scalar(
        select(func.coalesce(func.sum(ComplianceFlag.exposure_amount), Decimal("0"))).where(
            ComplianceFlag.project_id == project_id,
            ComplianceFlag.status == ComplianceFlagStatus.OPEN,
        )
    )
    if total is None:
        return Decimal("0")
    return Decimal(total)


def check_risk_cap(
    db: Session,
    project_id: UUID,
    criteria: EvaluationCriteria,
    winning_bid_value: Decimal | None = None,
) -> tuple[bool, Decimal, Decimal, Decimal]:
    """Return ``(breached, total_exposure, cap_amount, capped_penalty)``.

    Per the engineering spec, the cap base is the winning bid value (``P_eval``),
    NOT the project budget. If ``winning_bid_value`` is None or <= 0 (e.g. no
    bids have been submitted yet), the cap cannot be computed and we fall back
    to reporting ``breached=False`` with ``capped_penalty=total_exposure``.

    ``capped_penalty`` is the *effective* penalty after applying the cap:
    ``min(total_exposure, cap_amount)`` — this is the value that should be
    reported to the client and used in financial exposure simulations.
    """
    total_exposure = _sum_open_exposure(db, project_id)

    if winning_bid_value is None or winning_bid_value <= 0:
        # No bid context yet — cannot enforce cap, report uncapped.
        cap_amount = Decimal("0")
        breached = False
        capped_penalty = total_exposure
    else:
        cap_amount = (criteria.risk_cap_pct / Decimal("100")) * winning_bid_value
        breached = total_exposure > cap_amount
        capped_penalty = min(total_exposure, cap_amount)

    logger.debug(
        "risk_cap_check project_id=%s exposure=%s winning_bid=%s cap_pct=%s cap=%s breached=%s capped=%s",
        project_id,
        total_exposure,
        winning_bid_value,
        criteria.risk_cap_pct,
        cap_amount,
        breached,
        capped_penalty,
    )
    return breached, total_exposure, cap_amount, capped_penalty
