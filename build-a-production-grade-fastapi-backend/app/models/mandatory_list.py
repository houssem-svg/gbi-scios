import enum
import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.compliance import ComplianceFlag


class MandatoryStatus(str, enum.Enum):
    MANDATORY = "mandatory"
    ACTIVE = "active"
    INACTIVE = "inactive"


class MandatoryListItem(Base):
    __tablename__ = "mandatory_list_items"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    item_code: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    product_name: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    local_manufacturer: Mapped[str] = mapped_column(String(255), nullable=False)
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
