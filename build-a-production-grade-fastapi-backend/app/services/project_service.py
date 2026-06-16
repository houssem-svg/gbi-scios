from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectUpdate


def create_project(db: Session, payload: ProjectCreate, owner: User) -> Project:
    project = Project(
        project_name=payload.project_name.strip(),
        client_name=payload.client_name.strip(),
        sector=payload.sector.strip(),
        status=payload.status,
        owner_id=owner.id,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def list_projects(db: Session, owner: User, skip: int = 0, limit: int = 100) -> list[Project]:
    statement = (
        select(Project)
        .where(Project.owner_id == owner.id)
        .order_by(Project.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(db.scalars(statement).all())


def get_project(db: Session, project_id: UUID, owner: User) -> Project:
    project = db.get(Project, project_id)
    if project is None or project.owner_id != owner.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


def update_project(db: Session, project_id: UUID, payload: ProjectUpdate, owner: User) -> Project:
    project = get_project(db, project_id, owner)
    update_data = payload.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if isinstance(value, str):
            value = value.strip()
        setattr(project, field, value)

    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def delete_project(db: Session, project_id: UUID, owner: User) -> None:
    project = get_project(db, project_id, owner)
    db.delete(project)
    db.commit()
