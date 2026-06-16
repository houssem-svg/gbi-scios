import enum
import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.boq_item import BoQItem
    from app.models.compliance import ComplianceFlag
    from app.models.uploaded_file import UploadedFile
    from app.models.user import User


class ProjectStatus(str, enum.Enum):
    PLANNING = "Planning"
    ACTIVE = "Active"
    ON_HOLD = "On Hold"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    client_name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    sector: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    status: Mapped[ProjectStatus] = mapped_column(
        Enum(
            ProjectStatus,
            name="project_status",
            values_callable=lambda statuses: [status.value for status in statuses],
            validate_strings=True,
        ),
        nullable=False,
        default=ProjectStatus.PLANNING,
        server_default=ProjectStatus.PLANNING.value,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    owner: Mapped["User"] = relationship("User", back_populates="projects")
    uploaded_files: Mapped[list["UploadedFile"]] = relationship(
        "UploadedFile",
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    boq_items: Mapped[list["BoQItem"]] = relationship(
        "BoQItem",
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    compliance_flags: Mapped[list["ComplianceFlag"]] = relationship(
        "ComplianceFlag",
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
