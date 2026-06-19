# app/routers/reporting.py

from pathlib import Path
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.reporting import ReportGenerateRequest, ReportListResponse, ReportRead
from app.services.project_service import get_project
from app.services.reporting import ReportingService

router = APIRouter(
    prefix="/api/v1/reporting",
    tags=["Reporting Engine"],
)


@router.post("/generate", response_model=ReportRead, status_code=status.HTTP_201_CREATED)
def generate_project_report(
    request: ReportGenerateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ReportRead:
    """Generate an executive compliance & risk report (JSON payload + PDF)."""
    # Ownership check — prevents IDOR: only the project owner can generate reports.
    try:
        project_uuid = UUID(request.project_id)
    except (TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid project_id")
    get_project(db, project_uuid, current_user)
    return ReportingService.generate_report(db=db, request=request, user_id=str(current_user.id))


@router.get("/project/{project_id}", response_model=ReportListResponse, status_code=status.HTTP_200_OK)
def get_project_reports(
    project_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ReportListResponse:
    """List all reports generated for a given project (ownership-checked)."""
    get_project(db, project_id, current_user)
    reports = ReportingService.get_reports_by_project(db=db, project_id=str(project_id))
    return {"reports": reports, "total": len(reports)}


@router.get("/download/{report_id}", response_class=FileResponse, status_code=status.HTTP_200_OK)
def download_report_file(
    report_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> FileResponse:
    """Securely download the executive PDF for a report (ownership-checked in service)."""
    file_path_str = ReportingService.download_report(
        db=db, report_id=report_id, user_id=str(current_user.id)
    )
    file_name = Path(file_path_str).name
    return FileResponse(
        path=file_path_str,
        media_type="application/pdf",
        filename=file_name,
        headers={"Content-Disposition": f"attachment; filename={file_name}"},
    )
