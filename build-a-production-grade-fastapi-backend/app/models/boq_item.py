# app/models/boq_item.py

import enum
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.compliance import ComplianceFlag
    from app.models.project import Project
    from app.models.uploaded_file import UploadedFile


class SourcingType(str, enum.Enum):
    LOCAL = "local"
    IMPORTED = "imported"
    UNKNOWN = "unknown"


class BoQItem(Base):
    __tablename__ = "boq_items"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    uploaded_file_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("uploaded_files.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    item_code: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    total_price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    sourcing_type: Mapped[SourcingType] = mapped_column(
        Enum(
            SourcingType,
            name="sourcing_type",
            values_callable=lambda sourcing_types: [
                sourcing_type.value for sourcing_type in sourcing_types
            ],
            validate_strings=True,
        ),
        nullable=False,
        default=SourcingType.UNKNOWN,
        server_default=SourcingType.UNKNOWN.value,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

    project: Mapped["Project"] = relationship("Project", back_populates="boq_items")
    uploaded_file: Mapped["UploadedFile"] = relationship("UploadedFile", back_populates="boq_items")
    compliance_flags: Mapped[list["ComplianceFlag"]] = relationship(
        "ComplianceFlag",
        back_populates="boq_item",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )