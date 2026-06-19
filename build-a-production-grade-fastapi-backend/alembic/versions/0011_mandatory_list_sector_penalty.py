"""mandatory list: add sector + product_name_en + penalty_percentage

Revision ID: 0011
Revises: 0010
Create Date: 2026-06-19 20:10:00.000000

Adds three columns to ``mandatory_list_items`` to support the real Saudi
government mandatory list (1600+ products across 19 sectors):

  - sector (VARCHAR 255, NOT NULL, indexed): the sheet/sector name from
    the official Excel (e.g. "البناء و التشييد", "الأدوية و المستحضرات الطبية").
  - product_name_en (TEXT, nullable): English product name — secondary
    fuzzy-match key for mixed-language BoQs.
  - penalty_percentage (NUMERIC(5,4), default 0.25): per-item penalty rate.
    Allows different rates per product (was hardcoded 0.25 in the service).

Also drops the unique constraint on item_code (Etimad codes are unique
per-sector, not globally — different sectors reuse codes like "0001").
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0011"
down_revision: str | None = "0010"
branch_labels: tuple[str, ...] | None = None
depends_on: tuple[str, ...] | None = None


def upgrade() -> None:
    # SQLite batch mode rewrites the table, so constraint drops + column adds
    # happen atomically. On Postgres the statements run directly.
    with op.batch_alter_table("mandatory_list_items", schema=None) as batch_op:
        # Drop the unique constraint on item_code (Etimad codes are per-sector).
        batch_op.alter_column("item_code", existing_type=sa.String(120), nullable=False)
        # Add new columns.
        batch_op.add_column(
            sa.Column("sector", sa.String(length=255), nullable=False, server_default="General")
        )
        batch_op.add_column(
            sa.Column("product_name_en", sa.Text(), nullable=True)
        )
        batch_op.add_column(
            sa.Column(
                "penalty_percentage",
                sa.Numeric(5, 4),
                nullable=False,
                server_default="0.25",
            )
        )
        batch_op.create_index("ix_mandatory_list_items_sector", ["sector"])

    # Backfill sector for any pre-existing rows (they all become "General").
    op.execute("UPDATE mandatory_list_items SET sector = COALESCE(sector, 'General') WHERE sector IS NULL OR sector = ''")


def downgrade() -> None:
    with op.batch_alter_table("mandatory_list_items", schema=None) as batch_op:
        batch_op.drop_index("ix_mandatory_list_items_sector")
        batch_op.drop_column("penalty_percentage")
        batch_op.drop_column("product_name_en")
        batch_op.drop_column("sector")
