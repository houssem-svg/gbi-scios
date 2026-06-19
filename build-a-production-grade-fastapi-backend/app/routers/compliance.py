from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_compliance_officer
from app.models.user import User
from app.schemas.compliance import (
    ComplianceFlagRead,
    ComplianceScanResult,
    FlagStatusUpdate,
    MandatoryListUploadResult,
)
from app.services.compliance_service import (
    enrich_compliance_flag,
    list_project_compliance_flags,
    scan_project_compliance,
    update_flag_status,
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


@router.patch("/flags/{flag_id}", response_model=ComplianceFlagRead)
def change_flag_status(
    flag_id: UUID,
    payload: FlagStatusUpdate,
    db: Annotated[Session, Depends(get_db)],
    officer: Annotated[User, Depends(require_compliance_officer)],
) -> ComplianceFlagRead:
    """Waive or resolve a compliance flag.

    Only Admin/Consultant (compliance officer) roles may call this endpoint.
    Waiving enforces the project waiver cap (default 10% of budget) and records
    a full audit trail (who, when, why, optional waiver strategy link).
    """
    flag = update_flag_status(db, flag_id, payload, officer)
    return enrich_compliance_flag(flag)
