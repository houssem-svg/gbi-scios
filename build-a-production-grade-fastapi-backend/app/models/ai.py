"""AI insights / waiver strategy models.

Fixed per forensic audit BE-3 / BE-11:
- ``project_id`` is now a proper UUID FK to ``projects.id`` (was ``String``).
- ``WaiverStrategy.compliance_flag_id`` is now a required (NOT NULL) FK to
  ``compliance_flags.id`` so every waiver is traceable to the exact violation.
- Added waiver audit fields: ``approval_status``, ``approved_by``,
  ``approved_at``, ``waiver_amount`` (enables the waiver workflow + cap).
- ``datetime.utcnow`` replaced with timezone-aware ``datetime.now(UTC)``.
"""

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    ForeignKey,
    JSON,
    Numeric,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.project import Project


class AIInsight(Base):
    __tablename__ = "ai_insights"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    executive_summary: Mapped[str] = mapped_column(Text, nullable=False)
    optimization_actions: Mapped[list] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

    project: Mapped["Project"] = relationship("Project")


class ExecutiveRecommendation(Base):
    __tablename__ = "executive_recommendations"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    insight_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("ai_insights.id", ondelete="CASCADE"),
        nullable=False,
    )
    action_type: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    impact_score: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

    project: Mapped["Project"] = relationship("Project")
    insight: Mapped["AIInsight"] = relationship("AIInsight")


class WaiverStrategy(Base):
    __tablename__ = "waiver_strategies"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    compliance_flag_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("compliance_flags.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    justification: Mapped[str] = mapped_column(Text, nullable=False)
    compensating_control: Mapped[str] = mapped_column(Text, nullable=False)
    approval_probability: Mapped[str] = mapped_column(String(50), nullable=False)

    # Waiver workflow + audit (Task 4 business-logic audit).
    approval_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="PENDING",
        server_default="PENDING",
    )
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    waiver_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 2),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

    project: Mapped["Project"] = relationship("Project")
