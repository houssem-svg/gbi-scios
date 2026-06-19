"""risk + ai tables

Revision ID: 0006
Revises: 94bcd8cc92ab
Create Date: 2026-06-16 12:00:00.000000

Creates the risk_ledgers / exposure_simulations / risk_scenarios /
ai_insights / executive_recommendations / waiver_strategies tables that
previously existed only as SQLAlchemy models without a migration (BE-3).

UUIDs are stored as ``sa.String(length=36)`` on SQLite to match the
projects / boq_items / compliance_flags tables (migrations 0001-0005) so
FKs join correctly (the reports table 94bcd8cc92ab uses ``sa.Uuid()``
which is inconsistent — see BE-11 audit note).
"""
from __future__ import annotations


from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0006"
down_revision: str | None = "94bcd8cc92ab"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _uuid_type() -> sa.TypeEngine:
    """Match the existing projects/boq/compliance tables: String(36) on
    SQLite, native UUID on Postgres."""
    if op.get_context().dialect.name == "postgresql":
        return postgresql.UUID(as_uuid=True)
    return sa.String(length=36)


def upgrade() -> None:
    # --- risk_ledgers ------------------------------------------------------
    op.create_table(
        "risk_ledgers",
        sa.Column("id", _uuid_type(), nullable=False),
        sa.Column("project_id", _uuid_type(), nullable=False),
        sa.Column("compliance_flag_id", _uuid_type(), nullable=True),
        sa.Column("risk_type", sa.String(length=120), nullable=False),
        sa.Column("severity_level", sa.String(length=50), nullable=False),
        sa.Column("financial_exposure", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("probability_score", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("operational_impact", sa.String(length=255), nullable=True),
        sa.Column("recommendation", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_risk_ledgers_project_id"), "risk_ledgers", ["project_id"])

    # --- exposure_simulations ---------------------------------------------
    op.create_table(
        "exposure_simulations",
        sa.Column("id", _uuid_type(), nullable=False),
        sa.Column("project_id", _uuid_type(), nullable=False),
        sa.Column("scenario_name", sa.String(length=255), nullable=False),
        sa.Column("simulated_loss", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("win_probability", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("lc_score_impact", sa.Float(), server_default="0.0", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_exposure_simulations_project_id"),
        "exposure_simulations",
        ["project_id"],
    )

    # --- risk_scenarios ----------------------------------------------------
    op.create_table(
        "risk_scenarios",
        sa.Column("id", _uuid_type(), nullable=False),
        sa.Column("project_id", _uuid_type(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("mitigation_strategy", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), server_default="active", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_risk_scenarios_project_id"), "risk_scenarios", ["project_id"]
    )

    # --- ai_insights -------------------------------------------------------
    op.create_table(
        "ai_insights",
        sa.Column("id", _uuid_type(), nullable=False),
        sa.Column("project_id", _uuid_type(), nullable=False),
        sa.Column("executive_summary", sa.Text(), nullable=False),
        sa.Column("optimization_actions", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ai_insights_project_id"), "ai_insights", ["project_id"])

    # --- executive_recommendations ----------------------------------------
    op.create_table(
        "executive_recommendations",
        sa.Column("id", _uuid_type(), nullable=False),
        sa.Column("project_id", _uuid_type(), nullable=False),
        sa.Column("insight_id", _uuid_type(), nullable=False),
        sa.Column("action_type", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("impact_score", sa.String(length=50), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["insight_id"], ["ai_insights.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_executive_recommendations_project_id"),
        "executive_recommendations",
        ["project_id"],
    )

    # --- waiver_strategies -------------------------------------------------
    op.create_table(
        "waiver_strategies",
        sa.Column("id", _uuid_type(), nullable=False),
        sa.Column("project_id", _uuid_type(), nullable=False),
        sa.Column("compliance_flag_id", _uuid_type(), nullable=False),
        sa.Column("justification", sa.Text(), nullable=False),
        sa.Column("compensating_control", sa.Text(), nullable=False),
        sa.Column("approval_probability", sa.String(length=50), nullable=False),
        sa.Column(
            "approval_status",
            sa.String(length=20),
            server_default="PENDING",
            nullable=False,
        ),
        sa.Column("approved_by", _uuid_type(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("waiver_amount", sa.Numeric(18, 2), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["compliance_flag_id"], ["compliance_flags.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["approved_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_waiver_strategies_project_id"),
        "waiver_strategies",
        ["project_id"],
    )
    op.create_index(
        op.f("ix_waiver_strategies_compliance_flag_id"),
        "waiver_strategies",
        ["compliance_flag_id"],
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_waiver_strategies_compliance_flag_id"), table_name="waiver_strategies"
    )
    op.drop_index(op.f("ix_waiver_strategies_project_id"), table_name="waiver_strategies")
    op.drop_table("waiver_strategies")

    op.drop_index(
        op.f("ix_executive_recommendations_project_id"),
        table_name="executive_recommendations",
    )
    op.drop_table("executive_recommendations")

    op.drop_index(op.f("ix_ai_insights_project_id"), table_name="ai_insights")
    op.drop_table("ai_insights")

    op.drop_index(op.f("ix_risk_scenarios_project_id"), table_name="risk_scenarios")
    op.drop_table("risk_scenarios")

    op.drop_index(
        op.f("ix_exposure_simulations_project_id"), table_name="exposure_simulations"
    )
    op.drop_table("exposure_simulations")

    op.drop_index(op.f("ix_risk_ledgers_project_id"), table_name="risk_ledgers")
    op.drop_table("risk_ledgers")
