from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Annotated, List
import traceback

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.ai import AIInsight, WaiverStrategy
from app.schemas.ai import AIInsightRead, WaiverStrategyRead
from app.services.executive_summary_generator import generate_and_save_insights
from app.services.waiver_generator import generate_and_save_waiver

router = APIRouter(prefix="/api/v1/ai", tags=["AI Insights Engine"])

@router.post("/generate-insights/{project_id}")
async def create_insights(
    project_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    try:
        return await generate_and_save_insights(db, project_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=traceback.format_exc())

@router.post("/generate-waiver/{project_id}")
async def create_waiver_strategy(
    project_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    try:
        return await generate_and_save_waiver(db, project_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=traceback.format_exc())

@router.get("/project/{project_id}", response_model=List[AIInsightRead])
def get_project_insights(
    project_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    insights = db.query(AIInsight).filter(AIInsight.project_id == str(project_id)).all()
    return insights