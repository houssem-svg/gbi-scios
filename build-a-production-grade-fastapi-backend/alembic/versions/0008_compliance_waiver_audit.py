"""compliance flag waiver audit fields

Revision ID: 0008
Revises: 0007
Create Date: 2026-06-16 14:00:00.000000

Adds the waiver/resolution audit trail to compliance_flags (Rule 10 — Waiver Logic):
  - waived_by        (FK users.id, nullable, SET NULL on delete)
  - waived_at        (DateTime, nullable)
  - waiver_reason    (String, nullable)
  - waiver_strategy_id (FK waiver_strategies.id, nullable, SET NULL on delete)
  - updated_at       (DateTime, defaults to now)

Also expands the violation_type enum with new values (LOCAL_CONTENT_QUOTA_UNMET,
NON_RHQ_SUPPLIER, PAYROLL_LEAKAGE, RISK_CAP_BREACH) via a non-validated enum
expansion. On SQLite this is a no-op (enums stored as VARCHAR); on Postgres the
enum type is altered to add the new values.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: tuple[str, ...] | None = None
depends_on: tuple[str, ...] | None = None


def _uuid_type() -> sa.types.TypeEngine:
    """Match the existing compliance_flags column type (String(36) on SQLite)."""
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        return postgresql_UUID(as_uuid=True)
    return sa.String(length=36)


def upgrade() -> None:
    bind = op.get_bind()

    # New audit columns on compliance_flags.
    with op.batch_alter_table("compliance_flags", schema=None) as batch_op:
        batch_op.add_column(sa.Column("waived_by", _uuid_type(), nullable=True))
        batch_op.add_column(sa.Column("waived_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("waiver_reason", sa.String(length=1000), nullable=True))
        batch_op.add_column(sa.Column("waiver_strategy_id", _uuid_type(), nullable=True))
        batch_op.add_column(
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            )
        )
        batch_op.create_index("ix_compliance_flags_waived_by", ["waived_by"])
        batch_op.create_index("ix_compliance_flags_waiver_strategy_id", ["waiver_strategy_id"])

    # Foreign keys (best-effort; SQLite batch mode rewrites the table so FKs are safe).
    try:
        op.create_foreign_key(
            "fk_compliance_flags_waived_by_users",
            "compliance_flags",
            "users",
            ["waived_by"],
            ["id"],
            ondelete="SET NULL",
        )
    except Exception:
        pass
    try:
        op.create_foreign_key(
            "fk_compliance_flags_waiver_strategy_id_waiver_strategies",
            "compliance_flags",
            "waiver_strategies",
            ["waiver_strategy_id"],
            ["id"],
            ondelete="SET NULL",
        )
    except Exception:
        pass

    # Expand the violation_type enum on Postgres (no-op on SQLite where it's VARCHAR).
    if bind.dialect.name == "postgresql":
        for value in (
            "local_content_quota_unmet",
            "non_rhq_supplier",
            "payroll_leakage",
            "risk_cap_breach",
        ):
            op.execute(f"ALTER TYPE violation_type ADD VALUE IF NOT EXISTS '{value}'")


def downgrade() -> None:
    with op.batch_alter_table("compliance_flags", schema=None) as batch_op:
        batch_op.drop_index("ix_compliance_flags_waiver_strategy_id")
        batch_op.drop_index("ix_compliance_flags_waived_by")
        batch_op.drop_column("updated_at")
        batch_op.drop_column("waiver_strategy_id")
        batch_op.drop_column("waiver_reason")
        batch_op.drop_column("waived_at")
        batch_op.drop_column("waived_by")


# Lazy import to avoid hard dependency at module import time.
def postgresql_UUID(as_uuid: bool = True):  # noqa: N802 - mimic sa name
    from sqlalchemy.dialects.postgresql import UUID
    return UUID(as_uuid=as_uuid)
