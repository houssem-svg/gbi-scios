from pathlib import Path
from typing import Protocol
from uuid import UUID, uuid4

from fastapi import UploadFile

from app.core.config import settings


class StorageBackend(Protocol):
    def save(self, file: UploadFile, project_id: UUID, extension: str) -> str:
        ...

    def delete(self, storage_path: str) -> None:
        ...


class LocalStorageBackend:
    def __init__(self, base_dir: str) -> None:
        self.base_dir = Path(base_dir)

    def save(self, file: UploadFile, project_id: UUID, extension: str) -> str:
        project_dir = self.base_dir / str(project_id)
        project_dir.mkdir(parents=True, exist_ok=True)

        destination = project_dir / f"{uuid4()}{extension}"
        with destination.open("wb") as output:
            while chunk := file.file.read(1024 * 1024):
                output.write(chunk)

        return destination.as_posix()

    def delete(self, storage_path: str) -> None:
        path = Path(storage_path)
        resolved_path = path.resolve()
        resolved_base = self.base_dir.resolve()

        try:
            resolved_path.relative_to(resolved_base)
        except ValueError:
            return

        if resolved_path.exists() and resolved_path.is_file():
            resolved_path.unlink()


def get_storage_backend() -> StorageBackend:
    return LocalStorageBackend(settings.upload_storage_dir)
