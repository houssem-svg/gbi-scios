from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.uploaded_file import UploadedFileType


class UploadedFileRead(BaseModel):
    id: UUID
    project_id: UUID
    original_filename: str
    storage_path: str
    file_type: UploadedFileType
    uploaded_by: UUID
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)
