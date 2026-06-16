# app/routers/dashboard.py

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.dashboard import DashboardSummaryResponse
from app.services.dashboard import DashboardService

router = APIRouter(
    prefix="/api/v1/dashboard",
    tags=["Dashboard & Analytics"]
)

@router.get("/summary", response_model=DashboardSummaryResponse, status_code=status.HTTP_200_OK)
def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    جلب الإحصائيات والتحليلات الشاملة لكافة المشاريع والمخالفات الخاصة بالمستخدم الحالي.
    يُستخدم لتغذية الشاشة الرئيسية (Home Dashboard) في واجهة المستخدم.
    """
    return DashboardService.get_user_dashboard_summary(db=db, user_id=str(current_user.id))