import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.boq_item import BoQItem
from app.models.uploaded_file import UploadedFile, UploadedFileType
from app.models.user import User
from app.schemas.boq import BoQParseResult
from app.services.boq_parser import BoQParserResult, parse_boq_file
from app.services.project_service import get_project

logger = logging.getLogger(__name__)


def parse_boq_upload(db: Session, uploaded_file_id: UUID, current_user: User) -> BoQParseResult:
    uploaded_file = db.get(UploadedFile, uploaded_file_id)
    if uploaded_file is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Uploaded file not found")

    get_project(db, uploaded_file.project_id, current_user)
    if uploaded_file.file_type not in {UploadedFileType.CSV, UploadedFileType.EXCEL}:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only Excel and CSV uploads can be parsed as BoQ data",
        )

    try:
        parser_result = parse_boq_file(uploaded_file.storage_path)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stored upload file was not found",
        ) from exc

    if parser_result.validation_errors:
        for validation_error in parser_result.validation_errors:
            logger.warning(
                "Skipped invalid BoQ row",
                extra={
                    "uploaded_file_id": str(uploaded_file.id),
                    "project_id": str(uploaded_file.project_id),
                    "error": validation_error,
                },
            )

    if parser_result.validation_errors and not parser_result.rows:
        _write_parsing_audit_log(uploaded_file, parser_result)
        return BoQParseResult(
            parsed_rows=0,
            failed_rows=parser_result.failed_rows,
            validation_errors=parser_result.validation_errors,
            items=[],
        )

    boq_items = [
        BoQItem(
            project_id=uploaded_file.project_id,
            uploaded_file_id=uploaded_file.id,
            item_code=row.item_code,
            description=row.description,
            quantity=row.quantity,
            unit_price=row.unit_price,
            total_price=row.total_price,
            sourcing_type=row.sourcing_type,
        )
        for row in parser_result.rows
    ]

    db.execute(delete(BoQItem).where(BoQItem.uploaded_file_id == uploaded_file.id))
    db.add_all(boq_items)
    db.commit()
    # expire_on_commit=False in SessionLocal → boq_items attributes are still
    # populated; no need for per-row db.refresh (was N extra SELECTs).

    _write_parsing_audit_log(uploaded_file, parser_result)
    return BoQParseResult(
        parsed_rows=len(boq_items),
        failed_rows=parser_result.failed_rows,
        validation_errors=parser_result.validation_errors,
        items=boq_items,
    )


def list_project_boq_items(
    db: Session,
    project_id: UUID,
    current_user: User,
    skip: int = 0,
    limit: int = 100,
) -> list[BoQItem]:
    get_project(db, project_id, current_user)
    statement = (
        select(BoQItem)
        .where(BoQItem.project_id == project_id)
        .order_by(BoQItem.created_at.desc(), BoQItem.item_code.asc())
        .offset(skip)
        .limit(limit)
    )
    return list(db.scalars(statement).all())


def _write_parsing_audit_log(uploaded_file: UploadedFile, parser_result: BoQParserResult) -> None:
    log_dir = Path(settings.parsing_log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"{uploaded_file.id}.jsonl"
    payload = {
        "event": "boq_parse_completed",
        "uploaded_file_id": str(uploaded_file.id),
        "project_id": str(uploaded_file.project_id),
        "parsed_rows": len(parser_result.rows),
        "failed_rows": parser_result.failed_rows,
        "validation_errors": parser_result.validation_errors,
        "created_at": datetime.now(UTC).isoformat(),
    }

    with log_path.open("a", encoding="utf-8") as output:
        output.write(json.dumps(payload) + "\n")
