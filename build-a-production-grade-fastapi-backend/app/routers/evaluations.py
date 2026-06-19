"""Evaluations router — exposes the bid evaluation engine over HTTP.

Routes (all require ``get_current_user`` and enforce project ownership via
``project_service.get_project`` inside the service layer):

- GET    /api/v1/evaluations/criteria/{project_id}    → EvaluationCriteriaRead
- PUT    /api/v1/evaluations/criteria/{project_id}    → EvaluationCriteriaRead
- POST   /api/v1/evaluations/bids                     → BidRead (create)
- GET    /api/v1/evaluations/bids/{project_id}        → list[BidRead]
- POST   /api/v1/evaluations/run/{project_id}         → EvaluationRunResponse
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.bid import BidCreate, BidRead
from app.schemas.evaluation import (
    EvaluationCriteriaRead,
    EvaluationCriteriaUpdate,
    EvaluationRunResponse,
)
from app.services.bid_evaluation_service import (
    create_bid,
    get_or_create_criteria,
    list_bids,
    run_evaluation,
    update_criteria,
)

router = APIRouter(prefix="/api/v1/evaluations", tags=["Evaluations"])


@router.get("/criteria/{project_id}", response_model=EvaluationCriteriaRead)
def get_criteria_endpoint(
    project_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> EvaluationCriteriaRead:
    criteria = get_or_create_criteria(db, project_id, current_user)
    return EvaluationCriteriaRead.model_validate(criteria)


@router.put("/criteria/{project_id}", response_model=EvaluationCriteriaRead)
def update_criteria_endpoint(
    project_id: UUID,
    payload: EvaluationCriteriaUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> EvaluationCriteriaRead:
    criteria = update_criteria(db, project_id, payload, current_user)
    return EvaluationCriteriaRead.model_validate(criteria)


@router.post("/bids", response_model=BidRead, status_code=status.HTTP_201_CREATED)
def create_bid_endpoint(
    payload: BidCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> BidRead:
    bid = create_bid(db, payload.project_id, payload, current_user)
    return BidRead.model_validate(bid)


@router.get("/bids/{project_id}", response_model=list[BidRead])
def list_bids_endpoint(
    project_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[BidRead]:
    bids = list_bids(db, project_id, current_user)
    return [BidRead.model_validate(b) for b in bids]


@router.post("/run/{project_id}", response_model=EvaluationRunResponse)
def run_evaluation_endpoint(
    project_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> EvaluationRunResponse:
    return run_evaluation(db, project_id, current_user)
