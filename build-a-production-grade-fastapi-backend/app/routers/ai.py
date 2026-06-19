from typing import Annotated, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.ai import AIInsight
from app.models.user import User
from app.schemas.ai import AIInsightRead, WaiverStrategyRead
from app.services.executive_summary_generator import generate_and_save_insights
from app.services.project_service import get_project
from app.services.waiver_generator import generate_and_save_waiver

router = APIRouter(prefix="/api/v1/ai", tags=["AI Insights Engine"])


@router.post("/generate-insights/{project_id}", response_model=AIInsightRead)
async def create_insights(
    project_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> AIInsightRead:
    # Ownership check — prevents IDOR.
    get_project(db, project_id, current_user)
    return await generate_and_save_insights(db, project_id)


@router.post("/generate-waiver/{project_id}", response_model=WaiverStrategyRead)
async def create_waiver_strategy(
    project_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    flag_id: UUID = Query(..., description="The ComplianceFlag id this waiver applies to."),
) -> WaiverStrategyRead:
    # Ownership check — prevents IDOR. The waiver service additionally verifies the
    # flag belongs to this project and that the acting user has compliance-officer
    # privileges before persisting.
    get_project(db, project_id, current_user)
    return await generate_and_save_waiver(db, project_id, flag_id, current_user)


@router.get("/project/{project_id}", response_model=List[AIInsightRead])
def get_project_insights(
    project_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> List[AIInsightRead]:
    get_project(db, project_id, current_user)
    insights = (
        db.query(AIInsight)
        .filter(AIInsight.project_id == project_id)
        .order_by(AIInsight.created_at.desc())
        .all()
    )
    return insights
