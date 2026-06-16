import enum
import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.boq_item import BoQItem
    from app.models.project import Project
    from app.models.user import User


class UploadedFileType(str, enum.Enum):
    EXCEL = "Excel"
    CSV = "CSV"
    PDF = "PDF"


class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    file_type: Mapped[UploadedFileType] = mapped_column(
        Enum(
            UploadedFileType,
            name="uploaded_file_type",
            values_callable=lambda file_types: [file_type.value for file_type in file_types],
            validate_strings=True,
        ),
        nullable=False,
    )
    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

    project: Mapped["Project"] = relationship("Project", back_populates="uploaded_files")
    uploader: Mapped["User"] = relationship("User", back_populates="uploaded_files")
    boq_items: Mapped[list["BoQItem"]] = relationship(
        "BoQItem",
        back_populates="uploaded_file",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
