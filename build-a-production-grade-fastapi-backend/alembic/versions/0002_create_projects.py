"""create projects table

Revision ID: 0002_create_projects
Revises: 0001_create_users
Create Date: 2026-06-15 00:00:00.000000

"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0002_create_projects"
down_revision: str | None = "0001_create_users"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PROJECT_STATUSES = ("Planning", "Active", "On Hold", "Completed", "Cancelled")


def _uuid_type() -> sa.TypeEngine:
    if op.get_context().dialect.name == "postgresql":
        return postgresql.UUID(as_uuid=True)
    return sa.String(length=36)


def _status_type() -> sa.TypeEngine:
    if op.get_context().dialect.name == "postgresql":
        return postgresql.ENUM(*PROJECT_STATUSES, name="project_status")
    return sa.String(length=50)


def upgrade() -> None:
    status_type = _status_type()
    if op.get_context().dialect.name == "postgresql":
        status_type.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "projects",
        sa.Column("id", _uuid_type(), nullable=False),
        sa.Column("project_name", sa.String(length=255), nullable=False),
        sa.Column("client_name", sa.String(length=255), nullable=False),
        sa.Column("sector", sa.String(length=120), nullable=False),
        sa.Column("status", status_type, server_default="Planning", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("owner_id", _uuid_type(), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_projects_client_name"), "projects", ["client_name"], unique=False)
    op.create_index(op.f("ix_projects_owner_id"), "projects", ["owner_id"], unique=False)
    op.create_index(op.f("ix_projects_project_name"), "projects", ["project_name"], unique=False)
    op.create_index(op.f("ix_projects_sector"), "projects", ["sector"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_projects_sector"), table_name="projects")
    op.drop_index(op.f("ix_projects_project_name"), table_name="projects")
    op.drop_index(op.f("ix_projects_owner_id"), table_name="projects")
    op.drop_index(op.f("ix_projects_client_name"), table_name="projects")
    op.drop_table("projects")

    if op.get_context().dialect.name == "postgresql":
        status_type = postgresql.ENUM(*PROJECT_STATUSES, name="project_status")
        status_type.drop(op.get_bind(), checkfirst=True)
