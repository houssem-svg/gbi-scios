"""create compliance tables

Revision ID: 0005_create_compliance_tables
Revises: 0004_create_boq_items
Create Date: 2026-06-15 00:00:00.000000

"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0005_create_compliance_tables"
down_revision: str | None = "0004_create_boq_items"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

MANDATORY_STATUSES = ("mandatory", "active", "inactive")
VIOLATION_TYPES = ("imported_mandatory_item",)
COMPLIANCE_FLAG_STATUSES = ("open", "waived", "resolved")


def _uuid_type() -> sa.TypeEngine:
    if op.get_context().dialect.name == "postgresql":
        return postgresql.UUID(as_uuid=True)
    return sa.String(length=36)


def _enum_type(name: str, values: tuple[str, ...]) -> sa.TypeEngine:
    if op.get_context().dialect.name == "postgresql":
        return postgresql.ENUM(*values, name=name)
    return sa.String(length=50)


def upgrade() -> None:
    mandatory_status = _enum_type("mandatory_status", MANDATORY_STATUSES)
    violation_type = _enum_type("violation_type", VIOLATION_TYPES)
    flag_status = _enum_type("compliance_flag_status", COMPLIANCE_FLAG_STATUSES)

    if op.get_context().dialect.name == "postgresql":
        mandatory_status.create(op.get_bind(), checkfirst=True)
        violation_type.create(op.get_bind(), checkfirst=True)
        flag_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "mandatory_list_items",
        sa.Column("id", _uuid_type(), nullable=False),
        sa.Column("item_code", sa.String(length=120), nullable=False),
        sa.Column("product_name", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=255), nullable=False),
        sa.Column("local_manufacturer", sa.String(length=255), nullable=False),
        sa.Column("mandatory_status", mandatory_status, server_default="mandatory", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_mandatory_list_items_category"),
        "mandatory_list_items",
        ["category"],
        unique=False,
    )
    op.create_index(
        op.f("ix_mandatory_list_items_item_code"),
        "mandatory_list_items",
        ["item_code"],
        unique=True,
    )

    op.create_table(
        "compliance_flags",
        sa.Column("id", _uuid_type(), nullable=False),
        sa.Column("project_id", _uuid_type(), nullable=False),
        sa.Column("boq_item_id", _uuid_type(), nullable=False),
        sa.Column("mandatory_item_id", _uuid_type(), nullable=False),
        sa.Column(
            "violation_type",
            violation_type,
            server_default="imported_mandatory_item",
            nullable=False,
        ),
        sa.Column("penalty_percentage", sa.Numeric(5, 4), server_default="0.25", nullable=False),
        sa.Column("exposure_amount", sa.Numeric(18, 4), nullable=False),
        sa.Column("status", flag_status, server_default="open", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["boq_item_id"], ["boq_items.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["mandatory_item_id"], ["mandatory_list_items.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_compliance_flags_boq_item_id"), "compliance_flags", ["boq_item_id"])
    op.create_index(
        op.f("ix_compliance_flags_mandatory_item_id"),
        "compliance_flags",
        ["mandatory_item_id"],
    )
    op.create_index(op.f("ix_compliance_flags_project_id"), "compliance_flags", ["project_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_compliance_flags_project_id"), table_name="compliance_flags")
    op.drop_index(op.f("ix_compliance_flags_mandatory_item_id"), table_name="compliance_flags")
    op.drop_index(op.f("ix_compliance_flags_boq_item_id"), table_name="compliance_flags")
    op.drop_table("compliance_flags")
    op.drop_index(op.f("ix_mandatory_list_items_item_code"), table_name="mandatory_list_items")
    op.drop_index(op.f("ix_mandatory_list_items_category"), table_name="mandatory_list_items")
    op.drop_table("mandatory_list_items")

    if op.get_context().dialect.name == "postgresql":
        postgresql.ENUM(*COMPLIANCE_FLAG_STATUSES, name="compliance_flag_status").drop(
            op.get_bind(),
            checkfirst=True,
        )
        postgresql.ENUM(*VIOLATION_TYPES, name="violation_type").drop(
            op.get_bind(),
            checkfirst=True,
        )
        postgresql.ENUM(*MANDATORY_STATUSES, name="mandatory_status").drop(
            op.get_bind(),
            checkfirst=True,
        )
