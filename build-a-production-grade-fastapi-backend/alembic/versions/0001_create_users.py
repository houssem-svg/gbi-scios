"""create users table

Revision ID: 0001_create_users
Revises:
Create Date: 2026-06-15 00:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001_create_users"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

USER_ROLES = ("Admin", "Consultant", "Client")


def _uuid_type() -> sa.TypeEngine:
    if op.get_context().dialect.name == "postgresql":
        return postgresql.UUID(as_uuid=True)
    return sa.String(length=36)


def _role_type() -> sa.TypeEngine:
    if op.get_context().dialect.name == "postgresql":
        return postgresql.ENUM(*USER_ROLES, name="user_role")
    return sa.String(length=50)


def upgrade() -> None:
    user_role = _role_type()
    if op.get_context().dialect.name == "postgresql":
        user_role.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", _uuid_type(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("role", user_role, server_default="Client", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")

    if op.get_context().dialect.name == "postgresql":
        user_role = postgresql.ENUM(*USER_ROLES, name="user_role")
        user_role.drop(op.get_bind(), checkfirst=True)
