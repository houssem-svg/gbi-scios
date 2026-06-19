"""create boq items table

Revision ID: 0004_create_boq_items
Revises: 0003_create_uploaded_files
Create Date: 2026-06-15 00:00:00.000000

"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0004_create_boq_items"
down_revision: str | None = "0003_create_uploaded_files"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SOURCING_TYPES = ("local", "imported", "unknown")


def _uuid_type() -> sa.TypeEngine:
    if op.get_context().dialect.name == "postgresql":
        return postgresql.UUID(as_uuid=True)
    return sa.String(length=36)


def _sourcing_type() -> sa.TypeEngine:
    if op.get_context().dialect.name == "postgresql":
        return postgresql.ENUM(*SOURCING_TYPES, name="sourcing_type")
    return sa.String(length=50)


def upgrade() -> None:
    sourcing_type = _sourcing_type()
    if op.get_context().dialect.name == "postgresql":
        sourcing_type.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "boq_items",
        sa.Column("id", _uuid_type(), nullable=False),
        sa.Column("project_id", _uuid_type(), nullable=False),
        sa.Column("uploaded_file_id", _uuid_type(), nullable=False),
        sa.Column("item_code", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 4), nullable=False),
        sa.Column("unit_price", sa.Numeric(18, 4), nullable=False),
        sa.Column("total_price", sa.Numeric(18, 4), nullable=False),
        sa.Column("sourcing_type", sourcing_type, server_default="unknown", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["uploaded_file_id"], ["uploaded_files.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_boq_items_item_code"), "boq_items", ["item_code"], unique=False)
    op.create_index(op.f("ix_boq_items_project_id"), "boq_items", ["project_id"], unique=False)
    op.create_index(
        op.f("ix_boq_items_uploaded_file_id"),
        "boq_items",
        ["uploaded_file_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_boq_items_uploaded_file_id"), table_name="boq_items")
    op.drop_index(op.f("ix_boq_items_project_id"), table_name="boq_items")
    op.drop_index(op.f("ix_boq_items_item_code"), table_name="boq_items")
    op.drop_table("boq_items")

    if op.get_context().dialect.name == "postgresql":
        sourcing_type = postgresql.ENUM(*SOURCING_TYPES, name="sourcing_type")
        sourcing_type.drop(op.get_bind(), checkfirst=True)
