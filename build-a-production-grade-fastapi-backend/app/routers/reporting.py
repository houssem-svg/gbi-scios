# app/routers/reporting.py

from fastapi import APIRouter, Depends, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pathlib import Path

from app.core.database import get_db 
from app.core.dependencies import get_current_user 

from app.schemas.reporting import ReportGenerateRequest, ReportRead, ReportListResponse
from app.services.reporting import ReportingService

router = APIRouter(
    prefix="/api/v1/reporting",
    tags=["Reporting Engine"]
)

@router.post("/generate", response_model=ReportRead, status_code=status.HTTP_201_CREATED)
def generate_project_report(
    request: ReportGenerateRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    تجميع نتائج الامتثال، والمخاطر، والتقييم لإنشاء ملف بيانات التقرير التنفيذي وتوليد PDF.
    """
    return ReportingService.generate_report(db=db, request=request, user_id=str(current_user.id))

@router.get("/project/{project_id}", response_model=ReportListResponse, status_code=status.HTTP_200_OK)
def get_project_reports(
    project_id: str,  
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    جلب كافة التقارير التي تم إنشاؤها لمشروع معين وحالاتها المعالجة.
    """
    reports = ReportingService.get_reports_by_project(db=db, project_id=project_id)
    return {"data": reports, "total": len(reports)}

# --- المسار الجديد للتحميل الآمن (Secure File Download Endpoint) ---

@router.get("/download/{report_id}", response_class=FileResponse, status_code=status.HTTP_200_OK)
def download_report_file(
    report_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    مسار آمن لتحميل ملف الـ PDF التنفيذي الخاص بالتقرير.
    يتحقق من الهوية والصلاحيات قبل السماح بنقل الملف للمتصفح.
    """
    # 1. طلب التحقق وجلب المسار الآمن من طبقة الخدمات
    file_path_str = ReportingService.download_report(db=db, report_id=report_id, user_id=str(current_user.id))
    
    # 2. استخراج اسم الملف الصافي
    file_name = Path(file_path_str).name

    # 3. إرجاع الملف مع إجبار المتصفح على التحميل المباشر
    return FileResponse(
        path=file_path_str,
        media_type="application/pdf",
        filename=file_name,
        headers={"Content-Disposition": f"attachment; filename={file_name}"}
    )