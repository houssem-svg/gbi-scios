"""Risk intelligence models (RiskLedger, ExposureSimulation, RiskScenario).

Fixed per forensic audit BE-3 / BE-11:
- ``project_id`` is now a proper UUID FK to ``projects.id`` (was ``String``).
- ``datetime.utcnow`` replaced with timezone-aware ``datetime.now(UTC)``.
- Migrated to SQLAlchemy 2 ``Mapped`` / ``mapped_column`` style consistent with
  the other models (see ``app/models/compliance.py``).
"""

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.project import Project


class RiskLedger(Base):
    __tablename__ = "risk_ledgers"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    compliance_flag_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        nullable=True,
    )
    risk_type: Mapped[str] = mapped_column(String(120), nullable=False)
    severity_level: Mapped[str] = mapped_column(String(50), nullable=False)
    financial_exposure: Mapped[float] = mapped_column(
        Float, default=0.0, server_default="0.0"
    )
    probability_score: Mapped[float] = mapped_column(
        Float, default=0.0, server_default="0.0"
    )
    operational_impact: Mapped[str | None] = mapped_column(String(255), nullable=True)
    recommendation: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

    project: Mapped["Project"] = relationship("Project")


class ExposureSimulation(Base):
    __tablename__ = "exposure_simulations"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    scenario_name: Mapped[str] = mapped_column(String(255), nullable=False)
    simulated_loss: Mapped[float] = mapped_column(
        Float, default=0.0, server_default="0.0"
    )
    win_probability: Mapped[float] = mapped_column(
        Float, default=0.0, server_default="0.0"
    )
    lc_score_impact: Mapped[float] = mapped_column(
        Float, default=0.0, server_default="0.0"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

    project: Mapped["Project"] = relationship("Project")


class RiskScenario(Base):
    __tablename__ = "risk_scenarios"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    mitigation_strategy: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="active", server_default="active"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

    project: Mapped["Project"] = relationship("Project")
