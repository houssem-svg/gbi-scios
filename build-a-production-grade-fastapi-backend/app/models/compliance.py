import enum
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.boq_item import BoQItem
    from app.models.mandatory_list import MandatoryListItem
    from app.models.project import Project


class ViolationType(str, enum.Enum):
    IMPORTED_MANDATORY_ITEM = "imported_mandatory_item"


class ComplianceFlagStatus(str, enum.Enum):
    OPEN = "open"
    WAIVED = "waived"
    RESOLVED = "resolved"


class ComplianceFlag(Base):
    __tablename__ = "compliance_flags"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    boq_item_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("boq_items.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    mandatory_item_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("mandatory_list_items.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    violation_type: Mapped[ViolationType] = mapped_column(
        Enum(
            ViolationType,
            name="violation_type",
            values_callable=lambda violation_types: [
                violation_type.value for violation_type in violation_types
            ],
            validate_strings=True,
        ),
        nullable=False,
        default=ViolationType.IMPORTED_MANDATORY_ITEM,
        server_default=ViolationType.IMPORTED_MANDATORY_ITEM.value,
    )
    penalty_percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        default=Decimal("0.30"),
        server_default="0.30",
    )
    exposure_amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    status: Mapped[ComplianceFlagStatus] = mapped_column(
        Enum(
            ComplianceFlagStatus,
            name="compliance_flag_status",
            values_callable=lambda statuses: [status.value for status in statuses],
            validate_strings=True,
        ),
        nullable=False,
        default=ComplianceFlagStatus.OPEN,
        server_default=ComplianceFlagStatus.OPEN.value,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

    project: Mapped["Project"] = relationship("Project", back_populates="compliance_flags")
    boq_item: Mapped["BoQItem"] = relationship("BoQItem", back_populates="compliance_flags")
    mandatory_item: Mapped["MandatoryListItem"] = relationship(
        "MandatoryListItem",
        back_populates="compliance_flags",
    )
