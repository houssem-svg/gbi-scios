"""Evaluation models — stores criteria config + computed evaluation results.

Implements Saudi local-content procurement evaluation rules:
- 60/40 (LC/price) default
- 70/30 alternative
- 50/50 alternative
- CUSTOM user-defined weights
- SME 10% price preference (Monsha'at)
- Tadawul listed bonus
- RHQ eligibility gate
- Risk cap (% of project budget)
- Waiver cap
"""

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.bid import EvaluationFormula

if TYPE_CHECKING:
    from app.models.bid import Bid
    from app.models.project import Project


class EvaluationCriteria(Base):
    """Singleton-per-project evaluation configuration (one row per project)."""

    __tablename__ = "evaluation_criteria"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    formula: Mapped[EvaluationFormula] = mapped_column(
        Enum(
            EvaluationFormula,
            name="evaluation_formula",
            values_callable=lambda formulas: [f.value for f in formulas],
            validate_strings=True,
            create_type=False,
        ),
        nullable=False,
        default=EvaluationFormula.SIXTY_FORTY,
        server_default=EvaluationFormula.SIXTY_FORTY.value,
    )
    lc_weight: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("60.00"), server_default="60.00"
    )
    price_weight: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("40.00"), server_default="40.00"
    )
    sme_preference_pct: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("10.00"), server_default="10.00"
    )
    tadawul_bonus_pts: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("5.00"), server_default="5.00"
    )
    rhq_required: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    risk_cap_pct: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("25.00"), server_default="25.00"
    )
    waiver_cap_pct: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("10.00"), server_default="10.00"
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


class EvaluationResult(Base):
    """One computed evaluation result per bid (bid_id is unique)."""

    __tablename__ = "evaluation_results"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    bid_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("bids.id", ondelete="CASCADE"),
        index=True,
        unique=True,
        nullable=False,
    )
    effective_price: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    final_score: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    disqualified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    disqualification_reason: Mapped[str | None] = mapped_column(String(120), nullable=True)
    breakdown_json: Mapped[str] = mapped_column(Text, nullable=False)
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

    bid: Mapped["Bid"] = relationship("Bid", back_populates="evaluation_result")
    project: Mapped["Project"] = relationship("Project")
