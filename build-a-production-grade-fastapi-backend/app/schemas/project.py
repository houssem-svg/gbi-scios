from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.project import ProjectStatus


class ProjectBase(BaseModel):
    project_name: str = Field(min_length=2, max_length=255)
    client_name: str = Field(min_length=2, max_length=255)
    sector: str = Field(min_length=2, max_length=120)
    status: ProjectStatus = ProjectStatus.PLANNING


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    project_name: str | None = Field(default=None, min_length=2, max_length=255)
    client_name: str | None = Field(default=None, min_length=2, max_length=255)
    sector: str | None = Field(default=None, min_length=2, max_length=120)
    status: ProjectStatus | None = None


class ProjectRead(ProjectBase):
    id: UUID
    created_at: datetime
    owner_id: UUID

    model_config = ConfigDict(from_attributes=True)
