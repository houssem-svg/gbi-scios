"""Supplier model — captures Saudi procurement supplier attributes needed for
the local-content evaluation engine (Monsha'at SME status, Tadawul listing,
Regional Headquarters eligibility)."""

import enum
import uuid
from datetime import UTC, date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, DateTime, Enum, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.bid import Bid


class SupplierSizeCategory(str, enum.Enum):
    SMALL = "SMALL"
    MEDIUM = "MEDIUM"
    LARGE = "LARGE"


def _sme_default(context) -> bool:
    """Derive ``is_sme`` from ``size_category`` when the caller does not set it
    explicitly. SMALL and MEDIUM suppliers are treated as SMEs per Monsha'at."""
    category = context.get_current_parameters().get("size_category")
    if category is None:
        return False
    value = category.value if isinstance(category, SupplierSizeCategory) else str(category)
    return value in {SupplierSizeCategory.SMALL.value, SupplierSizeCategory.MEDIUM.value}


class Supplier(Base):
    __tablename__ = "suppliers"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    legal_name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    commercial_registration_no: Mapped[str] = mapped_column(
        String(120), unique=True, index=True, nullable=False
    )
    size_category: Mapped[SupplierSizeCategory] = mapped_column(
        Enum(
            SupplierSizeCategory,
            name="supplier_size_category",
            values_callable=lambda categories: [c.value for c in categories],
            validate_strings=True,
        ),
        nullable=False,
        default=SupplierSizeCategory.LARGE,
        server_default=SupplierSizeCategory.LARGE.value,
    )
    is_sme: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=_sme_default,
        server_default="false",
    )
    monshaat_certificate_no: Mapped[str | None] = mapped_column(String(120), nullable=True)
    monshaat_certificate_expiry: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_tadawul_listed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    tadawul_ticker: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_rhq_qualified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    rhq_license_no: Mapped[str | None] = mapped_column(String(120), nullable=True)
    rhq_license_expiry: Mapped[date | None] = mapped_column(Date, nullable=True)

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

    bids: Mapped[list["Bid"]] = relationship(
        "Bid", back_populates="supplier", passive_deletes=True
    )
