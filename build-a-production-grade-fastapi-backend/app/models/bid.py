"""Bid model + ``EvaluationFormula`` enum.

A Bid is a supplier's offer on a project. It carries the raw inputs
(submitted price, local-content score) and the computed outputs of the
evaluation engine (effective price after SME preference, final weighted
score, rank)."""

import enum
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
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.evaluation import EvaluationResult
    from app.models.project import Project
    from app.models.supplier import Supplier


class EvaluationFormula(str, enum.Enum):
    SIXTY_FORTY = "SIXTY_FORTY"
    SEVENTY_THIRTY = "SEVENTY_THIRTY"
    FIFTY_FIFTY = "FIFTY_FIFTY"
    CUSTOM = "CUSTOM"


class Bid(Base):
    __tablename__ = "bids"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    supplier_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("suppliers.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    submitted_price: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    local_content_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0"),
        server_default="0",
    )
    evaluation_formula: Mapped[EvaluationFormula] = mapped_column(
        Enum(
            EvaluationFormula,
            name="evaluation_formula",
            values_callable=lambda formulas: [f.value for f in formulas],
            validate_strings=True,
        ),
        nullable=False,
        default=EvaluationFormula.SIXTY_FORTY,
        server_default=EvaluationFormula.SIXTY_FORTY.value,
    )
    custom_lc_weight: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    custom_price_weight: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)

    # Pharma advantage: per the engineering spec (💡.docx Microservice 1, line 812-813):
    #   P_adjusted = P_eval × (1 - PharmaDiscountRate)
    # Optional per-bid discount rate (0.0–1.0) applied to the submitted price
    # BEFORE the SME preference and scoring. Default 0 (no pharma discount).
    pharma_discount_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        default=Decimal("0"),
        server_default="0",
    )
    pharma_discount_applied: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )

    sme_preference_applied: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    tadawul_bonus_applied: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )

    effective_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    final_score: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    rank: Mapped[int | None] = mapped_column(Integer, nullable=True)

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
    supplier: Mapped["Supplier"] = relationship("Supplier", back_populates="bids")
    evaluation_result: Mapped["EvaluationResult | None"] = relationship(
        "EvaluationResult",
        back_populates="bid",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
