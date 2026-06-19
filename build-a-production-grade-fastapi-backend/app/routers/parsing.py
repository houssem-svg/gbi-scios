from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.boq import BoQItemRead, BoQParseResult
from app.services.parsing_service import list_project_boq_items, parse_boq_upload

router = APIRouter()


@router.post("/boq/{uploaded_file_id}", response_model=BoQParseResult)
def parse_boq(
    uploaded_file_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> BoQParseResult:
    return parse_boq_upload(db, uploaded_file_id, current_user)


@router.get("/boq/project/{project_id}", response_model=list[BoQItemRead])
def list_boq_items(
    project_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[BoQItemRead]:
    return list_project_boq_items(db, project_id, current_user, skip=skip, limit=limit)
