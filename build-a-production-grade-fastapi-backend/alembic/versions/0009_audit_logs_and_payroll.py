"""system audit logs + payroll ledgers (LCP payroll recognition)

Revision ID: 0009
Revises: 0008
Create Date: 2026-06-16 15:00:00.000000

Creates two new tables:

1. ``system_audit_logs`` — immutable audit trail of state-changing actions
   (per the engineering spec 💡.docx Layer 4 schema).

2. ``payroll_ledgers`` — per-project payroll records used to compute the
   LCP payroll leakage (46.6% of Saudi payroll is value leakage outside
   the Kingdom; 53.4% is recognized as local content). Per the engineering
   spec (💡.docx Microservice 2, line 874 + JSON example line 1315-1323):

     PayrollLeakage = ExpatPayroll × 0.466   (the unrecognized portion)

   This migration only creates the schema; the leakage calculation lives in
   ``app.services.payroll_service``.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: tuple[str, ...] | None = None
depends_on: tuple[str, ...] | None = None


def _uuid_type() -> sa.types.TypeEngine:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        from sqlalchemy.dialects.postgresql import UUID
        return UUID(as_uuid=True)
    return sa.String(length=36)


def _audit_action_enum() -> sa.types.TypeEngine:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        return sa.Enum(
            "create", "update", "delete", "scan", "waive", "resolve",
            "evaluate", "generate", "login", "register",
            name="audit_action",
            validate_strings=True,
        )
    # SQLite: store as VARCHAR.
    return sa.String(length=40)


def upgrade() -> None:
    # 1. system_audit_logs
    op.create_table(
        "system_audit_logs",
        sa.Column("id", _uuid_type(), primary_key=True),
        sa.Column("user_id", _uuid_type(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", _audit_action_enum(), nullable=False),
        sa.Column("target_table", sa.String(length=80), nullable=False),
        sa.Column("target_id", sa.String(length=64), nullable=True),
        sa.Column("project_id", _uuid_type(), nullable=True),
        sa.Column("changes_json", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_system_audit_logs_user_id", "system_audit_logs", ["user_id"])
    op.create_index("ix_system_audit_logs_action", "system_audit_logs", ["action"])
    op.create_index("ix_system_audit_logs_target_table", "system_audit_logs", ["target_table"])
    op.create_index("ix_system_audit_logs_target_id", "system_audit_logs", ["target_id"])
    op.create_index("ix_system_audit_logs_project_id", "system_audit_logs", ["project_id"])
    op.create_index("ix_system_audit_logs_timestamp", "system_audit_logs", ["timestamp"])

    # 2. payroll_ledgers
    op.create_table(
        "payroll_ledgers",
        sa.Column("id", _uuid_type(), primary_key=True),
        sa.Column(
            "project_id",
            _uuid_type(),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("total_budget", sa.Numeric(18, 2), nullable=False),
        sa.Column("saudi_payroll", sa.Numeric(18, 2), nullable=False),
        sa.Column("expat_payroll", sa.Numeric(18, 2), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("source_file_id", _uuid_type(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_payroll_ledgers_project_id", "payroll_ledgers", ["project_id"])


def downgrade() -> None:
    op.drop_index("ix_payroll_ledgers_project_id", table_name="payroll_ledgers")
    op.drop_table("payroll_ledgers")
    op.drop_index("ix_system_audit_logs_timestamp", table_name="system_audit_logs")
    op.drop_index("ix_system_audit_logs_project_id", table_name="system_audit_logs")
    op.drop_index("ix_system_audit_logs_target_id", table_name="system_audit_logs")
    op.drop_index("ix_system_audit_logs_target_table", table_name="system_audit_logs")
    op.drop_index("ix_system_audit_logs_action", table_name="system_audit_logs")
    op.drop_index("ix_system_audit_logs_user_id", table_name="system_audit_logs")
    op.drop_table("system_audit_logs")
