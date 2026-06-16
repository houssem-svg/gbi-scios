from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.upload import UploadedFileRead
from app.services.upload_service import create_upload, delete_upload, list_project_uploads

router = APIRouter()


@router.post("", response_model=UploadedFileRead, status_code=status.HTTP_201_CREATED)
def upload_file(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    project_id: UUID = Form(...),
    file: UploadFile = File(...),
) -> UploadedFileRead:
    return create_upload(db, project_id, file, current_user)


@router.get("/project/{project_id}", response_model=list[UploadedFileRead])
def list_for_project(
    project_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[UploadedFileRead]:
    return list_project_uploads(db, project_id, current_user)


@router.delete("/{upload_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(
    upload_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Response:
    delete_upload(db, upload_id, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
