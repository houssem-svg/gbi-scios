"""Bid evaluation engine — implements the Saudi local-content procurement rules.

Rules implemented (Task 4 business-logic audit):
1. 60/40 weighted evaluation (LC score : price).
2. 70/30 weighted evaluation.
3. 50/50 weighted evaluation.
4. CUSTOM weighted evaluation (uses criteria.lc_weight / price_weight).
5. SME 10% price preference (Monsha'at-certified SMALL/MEDIUM suppliers).
6. Tadawul-listed supplier bonus on LC score.
7. RHQ eligibility gate (non-RHQ suppliers disqualified when required).
8. Risk cap (open exposure vs % of project budget).
"""

import json
import logging
from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session, selectinload

from app.models.bid import Bid, EvaluationFormula
from app.models.boq_item import BoQItem
from app.models.evaluation import EvaluationCriteria, EvaluationResult
from app.models.user import User
from app.schemas.bid import BidCreate
from app.schemas.evaluation import (
    EvaluationResultRead,
    EvaluationRunResponse,
)
from app.services.project_service import get_project
from app.services.risk_cap_service import check_risk_cap

logger = logging.getLogger(__name__)

_HUNDRED = Decimal("100")
_ZERO = Decimal("0")

# Static formula weight tables (Rules 1, 2).
# Per the engineering spec (💡.docx Microservice 1, line 799-805 + code 826-830):
#   60/40 model: FinalScore = (P_min/P_eval × 60) + (LC × 0.40)  → price_weight=60, lc_weight=40
#   70/30 model: FinalScore = (P_min/P_eval × 30) + (LC × 0.70)  → price_weight=30, lc_weight=70
#   50/50 model: equal weights.
# Verified against JSON payload example (line 1228-1248):
#   Client  bid=250M, lc=15, p_min=235M → financial=56.40 (=0.94×60), lc_score=6.00 (=15×0.40), final=62.40
#   Compet. bid=235M, lc=45, tadawul+5  → financial=60.00 (=1×60),   lc_score=18.00(=45×0.40), final=83.00
# Tuple order is (lc_weight, price_weight).
_FORMULA_WEIGHTS: dict[EvaluationFormula, tuple[Decimal, Decimal]] = {
    EvaluationFormula.SIXTY_FORTY: (Decimal("40"), Decimal("60")),
    EvaluationFormula.SEVENTY_THIRTY: (Decimal("70"), Decimal("30")),
    EvaluationFormula.FIFTY_FIFTY: (Decimal("50"), Decimal("50")),
}


def _resolve_weights(criteria: EvaluationCriteria) -> tuple[Decimal, Decimal]:
    """Return ``(lc_weight, price_weight)`` for the active formula."""
    if criteria.formula == EvaluationFormula.CUSTOM:
        return criteria.lc_weight, criteria.price_weight
    return _FORMULA_WEIGHTS.get(criteria.formula, (Decimal("40"), Decimal("60")))


def get_or_create_criteria(
    db: Session, project_id: UUID, current_user: User
) -> EvaluationCriteria:
    """Return the project's evaluation criteria row, creating a default one if
    none exists. Enforces project ownership."""
    get_project(db, project_id, current_user)

    criteria = db.scalar(
        select(EvaluationCriteria).where(EvaluationCriteria.project_id == project_id)
    )
    if criteria is None:
        criteria = EvaluationCriteria(project_id=project_id)
        db.add(criteria)
        db.commit()
        db.refresh(criteria)
    return criteria


def update_criteria(
    db: Session,
    project_id: UUID,
    payload,
    current_user: User,
) -> EvaluationCriteria:
    get_project(db, project_id, current_user)
    criteria = get_or_create_criteria(db, project_id, current_user)

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(criteria, field, value)

    # Keep lc_weight / price_weight in sync with the chosen formula for the
    # standard presets so the persisted row is internally consistent.
    if criteria.formula != EvaluationFormula.CUSTOM:
        lc_w, price_w = _FORMULA_WEIGHTS.get(
            criteria.formula, (Decimal("60"), Decimal("40"))
        )
        criteria.lc_weight = lc_w
        criteria.price_weight = price_w

    db.add(criteria)
    db.commit()
    db.refresh(criteria)
    return criteria


def create_bid(
    db: Session,
    project_id: UUID,
    payload: BidCreate,
    current_user: User,
) -> Bid:
    get_project(db, project_id, current_user)

    # project_id comes from the URL path; the BidCreate body does not carry it.

    if payload.evaluation_formula == EvaluationFormula.CUSTOM and (
        payload.custom_lc_weight is None or payload.custom_price_weight is None
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CUSTOM formula requires custom_lc_weight and custom_price_weight",
        )

    bid = Bid(
        project_id=project_id,
        supplier_id=payload.supplier_id,
        submitted_price=payload.submitted_price,
        local_content_score=payload.local_content_score,
        evaluation_formula=payload.evaluation_formula,
        custom_lc_weight=payload.custom_lc_weight,
        custom_price_weight=payload.custom_price_weight,
        pharma_discount_rate=payload.pharma_discount_rate,
    )
    db.add(bid)
    db.commit()
    db.refresh(bid)
    return bid


def list_bids(db: Session, project_id: UUID, current_user: User) -> list[Bid]:
    get_project(db, project_id, current_user)
    statement = (
        select(Bid)
        .where(Bid.project_id == project_id)
        .options(selectinload(Bid.supplier))
        .order_by(Bid.created_at.desc())
    )
    return list(db.scalars(statement).all())


def _disqualify(bid: Bid, reason: str, breakdown: dict) -> None:
    bid.sme_preference_applied = False
    bid.tadawul_bonus_applied = False
    bid.effective_price = bid.submitted_price
    bid.final_score = None
    bid.rank = None
    breakdown["disqualified"] = True
    breakdown["disqualification_reason"] = reason


def _monshaat_valid(supplier, today: date) -> bool:
    if not supplier.is_sme:
        return False
    if supplier.monshaat_certificate_expiry is None:
        # Without an expiry we cannot prove the certificate is current.
        return False
    return supplier.monshaat_certificate_expiry >= today


def _rhq_valid(supplier, today: date) -> bool:
    if not supplier.is_rhq_qualified:
        return False
    if supplier.rhq_license_expiry is None:
        return True
    return supplier.rhq_license_expiry >= today


def _project_budget(db: Session, project_id: UUID) -> Decimal:
    """Sum of BoQItem.total_price for the project (the Project model has no
    budget field — see Task 2-a audit note on ``reporting._build_exposure_metrics``)."""
    total = db.scalar(
        select(func.coalesce(func.sum(BoQItem.total_price), Decimal("0"))).where(
            BoQItem.project_id == project_id
        )
    )
    if total is None:
        return Decimal("0")
    return Decimal(total)


def run_evaluation(
    db: Session,
    project_id: UUID,
    current_user: User,
) -> EvaluationRunResponse:
    """Run the full evaluation pipeline for a project.

    1. Load criteria + all bids (with suppliers).
    2. Per bid: RHQ gate → SME preference → Tadawul bonus → weighted score.
    3. Rank non-disqualified bids by ``final_score`` desc.
    4. Upsert ``EvaluationResult`` rows (delete-then-add with flush).
    5. Compute risk cap via ``risk_cap_service``.
    6. Build and return ``EvaluationRunResponse``.
    """
    get_project(db, project_id, current_user)
    criteria = get_or_create_criteria(db, project_id, current_user)

    bids = list(
        db.scalars(
            select(Bid)
            .where(Bid.project_id == project_id)
            .options(selectinload(Bid.supplier))
        ).all()
    )

    lc_weight, price_weight = _resolve_weights(criteria)
    sme_pct = criteria.sme_preference_pct
    tadawul_bonus = criteria.tadawul_bonus_pts
    rhq_required = criteria.rhq_required
    today = date.today()

    computed: list[dict] = []
    for bid in bids:
        supplier = bid.supplier
        breakdown: dict = {
            "bid_id": str(bid.id),
            "supplier_id": str(supplier.id) if supplier else None,
            "supplier_legal_name": supplier.legal_name if supplier else None,
            "submitted_price": str(bid.submitted_price),
            "local_content_score": str(bid.local_content_score),
            "formula": criteria.formula.value,
            "lc_weight": str(lc_weight),
            "price_weight": str(price_weight),
            "sme_preference_pct": str(sme_pct),
            "tadawul_bonus_pts": str(tadawul_bonus),
            "rhq_required": rhq_required,
        }

        # --- RHQ eligibility gate (Rule 7) --------------------------------
        if rhq_required and (supplier is None or not _rhq_valid(supplier, today)):
            _disqualify(bid, "NON_RHQ_SUPPLIER", breakdown)
            computed.append(
                {
                    "bid": bid,
                    "effective_price": bid.submitted_price,
                    "final_score": _ZERO,
                    "rank": 0,
                    "disqualified": True,
                    "disqualification_reason": "NON_RHQ_SUPPLIER",
                    "breakdown": breakdown,
                }
            )
            continue

        effective_price = bid.submitted_price
        lc_score = bid.local_content_score

        # --- Pharma advantage (💡.docx Microservice 1, line 812-813) ------
        # P_adjusted = P_eval × (1 - PharmaDiscountRate)
        # Applied FIRST (before SME preference) per the spec's adjust_bid_price
        # code which applies pharma discount before SME.
        pharma_rate = bid.pharma_discount_rate or _ZERO
        if pharma_rate > 0:
            effective_price = effective_price * (_HUNDRED - pharma_rate * _HUNDRED) / _HUNDRED
            bid.pharma_discount_applied = True
        else:
            bid.pharma_discount_applied = False

        # --- SME 10% price preference (Rule 3) ---------------------------
        # Applied to the (already pharma-adjusted) price.
        if supplier is not None and _monshaat_valid(supplier, today):
            effective_price = effective_price * (_HUNDRED - sme_pct) / _HUNDRED
            bid.sme_preference_applied = True
        else:
            bid.sme_preference_applied = False

        # --- Tadawul listed bonus (Rule 4) --------------------------------
        # Per the engineering spec (💡.docx JSON example, line 1238-1248):
        #   competitor: financial_score=60.00, lc_score=18.00, tadawul_bonus=5.00, final=83.00
        #   83.00 = 60.00 + 18.00 + 5.00
        # The Tadawul bonus is added DIRECTLY to the final score AFTER the weighted
        # sum, NOT to the LC score before weighting.
        tadawul_bonus_pts = tadawul_bonus if (supplier is not None and supplier.is_tadawul_listed) else _ZERO
        bid.tadawul_bonus_applied = bool(tadawul_bonus_pts > 0)

        bid.effective_price = effective_price

        breakdown["effective_price"] = str(effective_price)
        breakdown["lc_score_raw"] = str(lc_score)
        breakdown["tadawul_bonus_pts"] = str(tadawul_bonus_pts)
        breakdown["pharma_discount_rate"] = str(pharma_rate)
        breakdown["pharma_discount_applied"] = bid.pharma_discount_applied
        breakdown["sme_preference_applied"] = bid.sme_preference_applied
        breakdown["tadawul_bonus_applied"] = bid.tadawul_bonus_applied

        computed.append(
            {
                "bid": bid,
                "effective_price": effective_price,
                "lc_score": lc_score,
                "tadawul_bonus_pts": tadawul_bonus_pts,
                "final_score": None,
                "rank": 0,
                "disqualified": False,
                "disqualification_reason": None,
                "breakdown": breakdown,
            }
        )

    # --- Weighted score (Rules 1, 2, 3, 4) ---------------------------------
    # Per the engineering spec (💡.docx line 799-805):
    #   FinalScore = (P_min/P_eval × price_weight) + (LC × lc_weight/100)
    # Then Tadawul bonus is added to the final score (not weighted).
    eligible = [c for c in computed if not c["disqualified"]]
    if eligible:
        lowest_price = min(c["effective_price"] for c in eligible)
        for c in eligible:
            price_score = (lowest_price / c["effective_price"]) * _HUNDRED
            weighted_score = (lc_weight / _HUNDRED) * c["lc_score"] + (
                price_weight / _HUNDRED
            ) * price_score
            # Tadawul bonus added AFTER weighting (per spec JSON example).
            final_score = weighted_score + c["tadawul_bonus_pts"]
            c["price_score"] = price_score
            c["weighted_score"] = weighted_score
            c["final_score"] = final_score
            c["bid"].final_score = final_score
            c["breakdown"]["price_score"] = str(price_score)
            c["breakdown"]["weighted_score"] = str(weighted_score)
            c["breakdown"]["tadawul_bonus_added"] = str(c["tadawul_bonus_pts"])
            c["breakdown"]["final_score"] = str(final_score)

        eligible.sort(key=lambda c: c["final_score"], reverse=True)
        for rank, c in enumerate(eligible, start=1):
            c["rank"] = rank
            c["bid"].rank = rank
            c["breakdown"]["rank"] = rank

    # --- Upsert EvaluationResult rows (delete-then-add, flush between) -----
    db.execute(delete(EvaluationResult).where(EvaluationResult.project_id == project_id))
    db.flush()

    new_results: list[EvaluationResult] = []
    for c in computed:
        er = EvaluationResult(
            project_id=project_id,
            bid_id=c["bid"].id,
            effective_price=c["effective_price"],
            final_score=c["final_score"] if c["final_score"] is not None else _ZERO,
            rank=c["rank"],
            disqualified=c["disqualified"],
            disqualification_reason=c["disqualification_reason"],
            breakdown_json=json.dumps(c["breakdown"], default=str, ensure_ascii=False),
            calculated_at=datetime.now(UTC),
        )
        db.add(er)
        new_results.append(er)

    # --- Risk cap (Rule 8) -------------------------------------------------
    # Per the engineering spec (💡.docx line 870):
    #   FinalPenalty = min(TotalCalculatedPenalties, P_eval × 0.20)
    # The cap base is the WINNING BID VALUE (lowest effective_price), not the
    # project budget. The capped_penalty is the effective penalty after clamping.
    winning_bid_value = _ZERO
    if eligible:
        winner = min(eligible, key=lambda c: c["effective_price"])
        winning_bid_value = winner["effective_price"]

    risk_cap_breached, total_exposure, cap_amount, capped_penalty = check_risk_cap(
        db, project_id, criteria, winning_bid_value=winning_bid_value
    )

    db.commit()
    for er in new_results:
        db.refresh(er)

    # Sort: eligible by rank asc, then disqualified at the end.
    sorted_results = sorted(
        new_results,
        key=lambda er: (er.disqualified, er.rank if not er.disqualified else 9999),
    )

    return EvaluationRunResponse(
        project_id=project_id,
        results=[EvaluationResultRead.model_validate(er) for er in sorted_results],
        risk_cap_breached=risk_cap_breached,
        risk_cap_pct=criteria.risk_cap_pct,
        total_exposure=total_exposure,
        project_budget=winning_bid_value,
    )
