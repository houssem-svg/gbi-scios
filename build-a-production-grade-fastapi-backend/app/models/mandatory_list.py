import enum
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, Numeric, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.compliance import ComplianceFlag


class MandatoryStatus(str, enum.Enum):
    MANDATORY = "mandatory"
    ACTIVE = "active"
    INACTIVE = "inactive"


class MandatoryListItem(Base):
    """A product on the Saudi government mandatory local-content list.

    Populated from the official ``القائمة الإلزامية للجهات الحكومية`` Excel
    workbook (19 sector sheets, ~1600 products). Each row carries:
      - item_code: the Etimad platform code (e.g. "0001", "2001").
      - product_name: Arabic product name (primary, used for fuzzy matching).
      - product_name_en: English product name (secondary match key).
      - sector: the sheet/sector name (e.g. "الأدوية و المستحضرات الطبية").
      - category: sub-category within the sector (segment title).
      - penalty_percentage: default 0.25 (25%) — applied when an imported
        BoQ item fuzzy-matches this mandatory item.
    """

    __tablename__ = "mandatory_list_items"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # Etimad code — unique within a sector but NOT globally (different sectors
    # may reuse codes), so we drop the unique constraint and index it instead.
    item_code: Mapped[str] = mapped_column(
        String(120), index=True, nullable=False
    )
    product_name: Mapped[str] = mapped_column(Text, nullable=False)
    # NEW: English name — improves fuzzy matching for mixed-language BoQs.
    product_name_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    # NEW: sector = the sheet name from the official Excel (e.g. "البناء و التشييد").
    sector: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    category: Mapped[str] = mapped_column(
        String(255), index=True, nullable=False, default="General"
    )
    local_manufacturer: Mapped[str] = mapped_column(
        String(255), nullable=False, default=""
    )
    # NEW: per-item penalty rate (default 25%). Allows the government to set
    # different rates per product (e.g. 15% for some, 30% for others).
    penalty_percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        default=Decimal("0.25"),
        server_default="0.25",
    )
    mandatory_status: Mapped[MandatoryStatus] = mapped_column(
        Enum(
            MandatoryStatus,
            name="mandatory_status",
            values_callable=lambda statuses: [status.value for status in statuses],
            validate_strings=True,
        ),
        nullable=False,
        default=MandatoryStatus.MANDATORY,
        server_default=MandatoryStatus.MANDATORY.value,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

    compliance_flags: Mapped[list["ComplianceFlag"]] = relationship(
        "ComplianceFlag",
        back_populates="mandatory_item",
        passive_deletes=True,
    )
