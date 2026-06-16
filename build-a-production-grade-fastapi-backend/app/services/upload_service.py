from pathlib import Path
from uuid import UUID

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.uploaded_file import UploadedFile, UploadedFileType
from app.models.user import User
from app.services.project_service import get_project
from app.services.storage_service import StorageBackend, get_storage_backend

ALLOWED_FILE_TYPES = {
    ".csv": UploadedFileType.CSV,
    ".pdf": UploadedFileType.PDF,
    ".xls": UploadedFileType.EXCEL,
    ".xlsx": UploadedFileType.EXCEL,
}

ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "text/csv",
    "application/csv",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}


def create_upload(
    db: Session,
    project_id: UUID,
    file: UploadFile,
    current_user: User,
    storage: StorageBackend | None = None,
) -> UploadedFile:
    file_type, extension = _validate_upload_file(file)
    get_project(db, project_id, current_user)

    storage_backend = storage or get_storage_backend()
    storage_path = storage_backend.save(file, project_id, extension)

    uploaded_file = UploadedFile(
        project_id=project_id,
        original_filename=Path(file.filename or "").name,
        storage_path=storage_path,
        file_type=file_type,
        uploaded_by=current_user.id,
    )
    db.add(uploaded_file)
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        storage_backend.delete(storage_path)
        raise

    db.refresh(uploaded_file)
    return uploaded_file


def list_project_uploads(db: Session, project_id: UUID, current_user: User) -> list[UploadedFile]:
    get_project(db, project_id, current_user)
    statement = (
        select(UploadedFile)
        .where(UploadedFile.project_id == project_id)
        .order_by(UploadedFile.uploaded_at.desc())
    )
    return list(db.scalars(statement).all())


def delete_upload(
    db: Session,
    upload_id: UUID,
    current_user: User,
    storage: StorageBackend | None = None,
) -> None:
    uploaded_file = db.get(UploadedFile, upload_id)
    if uploaded_file is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Uploaded file not found")

    get_project(db, uploaded_file.project_id, current_user)
    storage_backend = storage or get_storage_backend()
    storage_path = uploaded_file.storage_path

    db.delete(uploaded_file)
    db.commit()
    storage_backend.delete(storage_path)


def _validate_upload_file(file: UploadFile) -> tuple[UploadedFileType, str]:
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File name is required")

    extension = Path(file.filename).suffix.lower()
    file_type = ALLOWED_FILE_TYPES.get(extension)
    if file_type is None:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only Excel, CSV, and PDF files are supported",
        )

    if file.content_type and file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported file content type",
        )

    _validate_file_size(file)
    return file_type, extension


def _validate_file_size(file: UploadFile) -> None:
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)

    if size <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty")

    if size > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Uploaded file exceeds {settings.max_upload_size_mb} MB",
        )
