"""Payroll ledger model — per-project payroll records.

Per the engineering spec (💡.docx Layer 2 schema `payroll_ledgers`):
  - total_budget: total payroll budget for the period.
  - saudi_payroll: amount paid to Saudi employees.
  - expat_payroll: amount paid to non-Saudi employees.

Used by ``payroll_service.calculate_payroll_leakage`` to compute the LCP
payroll leakage (46.6% of expat payroll is value leakage outside the Kingdom;
53.4% of Saudi payroll is recognized as local content).
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.project import Project


class PayrollLedger(Base):
    __tablename__ = "payroll_ledgers"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    total_budget: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    saudi_payroll: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    expat_payroll: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    source_file_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

    project: Mapped["Project"] = relationship("Project")
