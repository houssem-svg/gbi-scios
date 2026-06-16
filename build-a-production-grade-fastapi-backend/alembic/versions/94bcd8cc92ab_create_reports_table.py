"""create reports table

Revision ID: 94bcd8cc92ab
Revises: 0005_create_compliance_tables
Create Date: 2026-06-15 19:32:38.756336

"""
from collections.abc import Sequence
from alembic import op
import sqlalchemy as sa

# التعريفات الأساسية للملف
revision: str = '94bcd8cc92ab'
down_revision: str | None = '0005_create_compliance_tables'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # إنشاء جدول التقارير بشكل متوافق تماماً مع SQLite و PostgreSQL
    op.create_table(
        'reports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Uuid(), nullable=False),
        sa.Column('generated_by', sa.Uuid(), nullable=True),
        sa.Column('report_type', sa.String(), nullable=False, server_default='EXECUTIVE'),
        sa.Column('status', sa.String(), nullable=False, server_default='PENDING'),
        # التصحيح هنا: استخدام sa.JSON() العام ليدعمه الطرفان بنجاح
        sa.Column('json_payload', sa.JSON(), nullable=True), 
        sa.Column('file_path', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['generated_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    # إنشاء الفهرس لسرعة الاستعلام
    op.create_index(op.f('ix_reports_id'), 'reports', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_reports_id'), table_name='reports')
    op.drop_table('reports')
