"""bid pharma discount columns

Revision ID: 0010
Revises: 0009
Create Date: 2026-06-16 16:00:00.000000

Adds two columns to the ``bids`` table for the pharma advantage adjustment
per the engineering spec (💡.docx Microservice 1, line 812-813):

    P_adjusted = P_eval × (1 - PharmaDiscountRate)

- ``pharma_discount_rate`` (Numeric(5,4), default 0): the discount rate (0.0–1.0).
- ``pharma_discount_applied`` (Boolean, default false): whether the rate was
  applied during the last evaluation run.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: tuple[str, ...] | None = None
depends_on: tuple[str, ...] | None = None


def upgrade() -> None:
    with op.batch_alter_table("bids", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "pharma_discount_rate",
                sa.Numeric(5, 4),
                nullable=False,
                server_default="0",
            )
        )
        batch_op.add_column(
            sa.Column(
                "pharma_discount_applied",
                sa.Boolean(),
                nullable=False,
                server_default="false",
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("bids", schema=None) as batch_op:
        batch_op.drop_column("pharma_discount_applied")
        batch_op.drop_column("pharma_discount_rate")
