from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.compliance import (
    ComplianceFlagRead,
    ComplianceScanResult,
    MandatoryListUploadResult,
)
from app.services.compliance_service import (
    enrich_compliance_flag,
    list_project_compliance_flags,
    scan_project_compliance,
    upload_mandatory_list,
)

router = APIRouter()


@router.post(
    "/mandatory-list/upload",
    response_model=MandatoryListUploadResult,
    status_code=status.HTTP_201_CREATED,
)
def upload_mandatory_list_file(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    file: UploadFile = File(...),
) -> MandatoryListUploadResult:
    return upload_mandatory_list(db, file)


@router.post("/scan/{project_id}", response_model=ComplianceScanResult)
def scan_project(
    project_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ComplianceScanResult:
    return scan_project_compliance(db, project_id, current_user)


@router.get("/project/{project_id}", response_model=list[ComplianceFlagRead])
def list_flags(
    project_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[ComplianceFlagRead]:
    flags = list_project_compliance_flags(db, project_id, current_user)
    return [enrich_compliance_flag(flag) for flag in flags]
