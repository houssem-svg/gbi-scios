"""evaluation tables

Revision ID: 0007
Revises: 0006
Create Date: 2026-06-16 13:00:00.000000

Creates the suppliers / evaluation_criteria / bids / evaluation_results
tables that implement the Saudi local-content bid evaluation engine
(60/40, 70/30, 50/50, CUSTOM formulas, SME 10% preference, Tadawul bonus,
RHQ eligibility gate, risk cap).

UUIDs are stored as ``sa.String(length=36)`` on SQLite to match the
projects / boq_items / compliance_flags tables.
"""
from __future__ import annotations


from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


SUPPLIER_SIZE_CATEGORIES = ("SMALL", "MEDIUM", "LARGE")
EVALUATION_FORMULAS = ("SIXTY_FORTY", "SEVENTY_THIRTY", "FIFTY_FIFTY", "CUSTOM")


def _uuid_type() -> sa.TypeEngine:
    if op.get_context().dialect.name == "postgresql":
        return postgresql.UUID(as_uuid=True)
    return sa.String(length=36)


def _enum_type(name: str, values: tuple[str, ...]) -> sa.TypeEngine:
    if op.get_context().dialect.name == "postgresql":
        return postgresql.ENUM(*values, name=name)
    return sa.String(length=50)


def upgrade() -> None:
    supplier_size = _enum_type("supplier_size_category", SUPPLIER_SIZE_CATEGORIES)
    eval_formula = _enum_type("evaluation_formula", EVALUATION_FORMULAS)

    if op.get_context().dialect.name == "postgresql":
        supplier_size.create(op.get_bind(), checkfirst=True)
        # NB: evaluation_formula enum may already be created by a future
        # migration on the bids table; create_type=False on the model avoids
        # double-creation. We still call .create(checkfirst=True) here for
        # safety on fresh databases.
        eval_formula.create(op.get_bind(), checkfirst=True)

    # --- suppliers ---------------------------------------------------------
    op.create_table(
        "suppliers",
        sa.Column("id", _uuid_type(), nullable=False),
        sa.Column("legal_name", sa.String(length=255), nullable=False),
        sa.Column(
            "commercial_registration_no", sa.String(length=120), nullable=False
        ),
        sa.Column(
            "size_category",
            supplier_size,
            server_default="LARGE",
            nullable=False,
        ),
        sa.Column("is_sme", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("monshaat_certificate_no", sa.String(length=120), nullable=True),
        sa.Column("monshaat_certificate_expiry", sa.Date(), nullable=True),
        sa.Column(
            "is_tadawul_listed", sa.Boolean(), server_default="false", nullable=False
        ),
        sa.Column("tadawul_ticker", sa.String(length=20), nullable=True),
        sa.Column(
            "is_rhq_qualified", sa.Boolean(), server_default="false", nullable=False
        ),
        sa.Column("rhq_license_no", sa.String(length=120), nullable=True),
        sa.Column("rhq_license_expiry", sa.Date(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "commercial_registration_no",
            name="uq_suppliers_commercial_registration_no",
        ),
    )
    op.create_index(op.f("ix_suppliers_legal_name"), "suppliers", ["legal_name"])
    op.create_index(
        op.f("ix_suppliers_commercial_registration_no"),
        "suppliers",
        ["commercial_registration_no"],
    )

    # --- evaluation_criteria ----------------------------------------------
    op.create_table(
        "evaluation_criteria",
        sa.Column("id", _uuid_type(), nullable=False),
        sa.Column("project_id", _uuid_type(), nullable=False),
        sa.Column(
            "formula",
            eval_formula,
            server_default="SIXTY_FORTY",
            nullable=False,
        ),
        sa.Column(
            "lc_weight", sa.Numeric(5, 2), server_default="60.00", nullable=False
        ),
        sa.Column(
            "price_weight", sa.Numeric(5, 2), server_default="40.00", nullable=False
        ),
        sa.Column(
            "sme_preference_pct",
            sa.Numeric(5, 2),
            server_default="10.00",
            nullable=False,
        ),
        sa.Column(
            "tadawul_bonus_pts",
            sa.Numeric(5, 2),
            server_default="5.00",
            nullable=False,
        ),
        sa.Column(
            "rhq_required", sa.Boolean(), server_default="false", nullable=False
        ),
        sa.Column(
            "risk_cap_pct",
            sa.Numeric(5, 2),
            server_default="25.00",
            nullable=False,
        ),
        sa.Column(
            "waiver_cap_pct",
            sa.Numeric(5, 2),
            server_default="10.00",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", name="uq_evaluation_criteria_project_id"),
    )

    # --- bids --------------------------------------------------------------
    op.create_table(
        "bids",
        sa.Column("id", _uuid_type(), nullable=False),
        sa.Column("project_id", _uuid_type(), nullable=False),
        sa.Column("supplier_id", _uuid_type(), nullable=False),
        sa.Column("submitted_price", sa.Numeric(18, 2), nullable=False),
        sa.Column(
            "local_content_score",
            sa.Numeric(5, 2),
            server_default="0",
            nullable=False,
        ),
        sa.Column(
            "evaluation_formula",
            eval_formula,
            server_default="SIXTY_FORTY",
            nullable=False,
        ),
        sa.Column("custom_lc_weight", sa.Numeric(5, 2), nullable=True),
        sa.Column("custom_price_weight", sa.Numeric(5, 2), nullable=True),
        sa.Column(
            "sme_preference_applied",
            sa.Boolean(),
            server_default="false",
            nullable=False,
        ),
        sa.Column(
            "tadawul_bonus_applied",
            sa.Boolean(),
            server_default="false",
            nullable=False,
        ),
        sa.Column("effective_price", sa.Numeric(18, 2), nullable=True),
        sa.Column("final_score", sa.Numeric(8, 4), nullable=True),
        sa.Column("rank", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["supplier_id"], ["suppliers.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_bids_project_id"), "bids", ["project_id"])
    op.create_index(op.f("ix_bids_supplier_id"), "bids", ["supplier_id"])

    # --- evaluation_results -----------------------------------------------
    op.create_table(
        "evaluation_results",
        sa.Column("id", _uuid_type(), nullable=False),
        sa.Column("project_id", _uuid_type(), nullable=False),
        sa.Column("bid_id", _uuid_type(), nullable=False),
        sa.Column("effective_price", sa.Numeric(18, 2), nullable=False),
        sa.Column("final_score", sa.Numeric(8, 4), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column(
            "disqualified", sa.Boolean(), server_default="false", nullable=False
        ),
        sa.Column("disqualification_reason", sa.String(length=120), nullable=True),
        sa.Column("breakdown_json", sa.Text(), nullable=False),
        sa.Column(
            "calculated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["bid_id"], ["bids.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("bid_id", name="uq_evaluation_results_bid_id"),
    )
    op.create_index(
        op.f("ix_evaluation_results_project_id"),
        "evaluation_results",
        ["project_id"],
    )
    op.create_index(
        op.f("ix_evaluation_results_bid_id"), "evaluation_results", ["bid_id"]
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_evaluation_results_bid_id"), table_name="evaluation_results"
    )
    op.drop_index(
        op.f("ix_evaluation_results_project_id"), table_name="evaluation_results"
    )
    op.drop_table("evaluation_results")

    op.drop_index(op.f("ix_bids_supplier_id"), table_name="bids")
    op.drop_index(op.f("ix_bids_project_id"), table_name="bids")
    op.drop_table("bids")

    op.drop_table("evaluation_criteria")

    op.drop_index(
        op.f("ix_suppliers_commercial_registration_no"), table_name="suppliers"
    )
    op.drop_index(op.f("ix_suppliers_legal_name"), table_name="suppliers")
    op.drop_table("suppliers")

    if op.get_context().dialect.name == "postgresql":
        postgresql.ENUM(*EVALUATION_FORMULAS, name="evaluation_formula").drop(
            op.get_bind(), checkfirst=True
        )
        postgresql.ENUM(*SUPPLIER_SIZE_CATEGORIES, name="supplier_size_category").drop(
            op.get_bind(), checkfirst=True
        )
