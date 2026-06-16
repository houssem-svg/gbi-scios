"""create uploaded files table

Revision ID: 0003_create_uploaded_files
Revises: 0002_create_projects
Create Date: 2026-06-15 00:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0003_create_uploaded_files"
down_revision: str | None = "0002_create_projects"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

UPLOADED_FILE_TYPES = ("Excel", "CSV", "PDF")


def _uuid_type() -> sa.TypeEngine:
    if op.get_context().dialect.name == "postgresql":
        return postgresql.UUID(as_uuid=True)
    return sa.String(length=36)


def _file_type() -> sa.TypeEngine:
    if op.get_context().dialect.name == "postgresql":
        return postgresql.ENUM(*UPLOADED_FILE_TYPES, name="uploaded_file_type")
    return sa.String(length=50)


def upgrade() -> None:
    file_type = _file_type()
    if op.get_context().dialect.name == "postgresql":
        file_type.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "uploaded_files",
        sa.Column("id", _uuid_type(), nullable=False),
        sa.Column("project_id", _uuid_type(), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("storage_path", sa.String(length=1024), nullable=False),
        sa.Column("file_type", file_type, nullable=False),
        sa.Column("uploaded_by", _uuid_type(), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_uploaded_files_project_id"), "uploaded_files", ["project_id"], unique=False)
    op.create_index(op.f("ix_uploaded_files_uploaded_by"), "uploaded_files", ["uploaded_by"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_uploaded_files_uploaded_by"), table_name="uploaded_files")
    op.drop_index(op.f("ix_uploaded_files_project_id"), table_name="uploaded_files")
    op.drop_table("uploaded_files")

    if op.get_context().dialect.name == "postgresql":
        file_type = postgresql.ENUM(*UPLOADED_FILE_TYPES, name="uploaded_file_type")
        file_type.drop(op.get_bind(), checkfirst=True)
