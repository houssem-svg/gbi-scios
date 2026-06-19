"""Monte-Carlo placeholder simulation engine.

Updated to be tolerant of an optional DB-backed ``base_exposure``:

- The new signature ``run_simulation(reduce_imports_pct, restructure_payroll_pct,
  base_exposure=None, project_id=None, db=None)`` keeps the existing keyword
  callers in ``app/routers/risk.py`` working unchanged.
- When ``base_exposure`` is not provided but ``db`` and ``project_id`` are,
  the real open-flag exposure is summed from ``compliance_flags`` and used as
  the base exposure (was previously hardcoded to 1,000,000 — see Task 2-a
  audit note on ``simulation_engine.run_simulation``).
"""

import logging
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.compliance import ComplianceFlag, ComplianceFlagStatus

logger = logging.getLogger(__name__)


def _fetch_open_exposure(db: Session, project_id: UUID) -> float:
    total = db.scalar(
        select(func.coalesce(func.sum(ComplianceFlag.exposure_amount), 0)).where(
            ComplianceFlag.project_id == project_id,
            ComplianceFlag.status == ComplianceFlagStatus.OPEN,
        )
    )
    if total is None:
        return 0.0
    return float(total)


def run_simulation(
    reduce_imports_pct: float,
    restructure_payroll_pct: float,
    base_exposure: float | None = None,
    project_id: UUID | None = None,
    db: Session | None = None,
) -> dict:
    """Run a placeholder exposure simulation.

    Args:
        reduce_imports_pct: fraction (0-1) by which import exposure is reduced.
        restructure_payroll_pct: fraction (0-1) by which payroll leakage is
            reduced.
        base_exposure: optional explicit base exposure (SAR). If omitted and
            both ``project_id`` and ``db`` are supplied, the open-flag
            exposure for the project is loaded from the DB. Otherwise 0.
        project_id: optional project to look up base exposure for.
        db: optional SQLAlchemy session used for the lookup.

    Returns:
        dict with ``simulated_loss``, ``win_probability``, ``lc_score_impact``.
    """
    if base_exposure is None:
        if db is not None and project_id is not None:
            base_exposure = _fetch_open_exposure(db, project_id)
            logger.debug(
                "simulation_engine loaded base_exposure=%s from DB for project_id=%s",
                base_exposure,
                project_id,
            )
        else:
            base_exposure = 0.0

    # Future integration: Monte Carlo algorithms go here.
    simulated_loss = base_exposure * (1.0 - reduce_imports_pct) * (
        1.0 - restructure_payroll_pct
    )

    # Simple probability mock logic based on exposure reduction.
    win_probability = 40.0 + (reduce_imports_pct * 100) + (restructure_payroll_pct * 50)
    win_probability = min(win_probability, 99.0)  # Max 99%

    lc_score_impact = (reduce_imports_pct + restructure_payroll_pct) * 10.0

    return {
        "simulated_loss": round(simulated_loss, 2),
        "win_probability": round(win_probability, 2),
        "lc_score_impact": round(lc_score_impact, 2),
    }
