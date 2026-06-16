from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "GBI-SCIOS API"
    environment: str = "local"
    api_v1_prefix: str = "/api/v1"

    database_url: str = Field(..., validation_alias="DATABASE_URL")
    upload_storage_dir: str = "storage/uploads"
    max_upload_size_mb: int = 25
    parsing_log_dir: str = "storage/parsing_logs"
    compliance_scan_log_dir: str = "storage/compliance_scan_logs"
    compliance_fuzzy_match_threshold: int = 85

    jwt_secret_key: str = Field(..., validation_alias="JWT_SECRET_KEY")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    @model_validator(mode="after")
    def normalize_local_paths(self) -> "Settings":
        if self.database_url.startswith("sqlite:///./"):
            db_path = BACKEND_ROOT / self.database_url.removeprefix("sqlite:///./")
            self.database_url = f"sqlite:///{db_path.as_posix()}"

        for field_name in ("upload_storage_dir", "parsing_log_dir", "compliance_scan_log_dir"):
            value = getattr(self, field_name)
            path = Path(value)
            if not path.is_absolute():
                setattr(self, field_name, str(BACKEND_ROOT / path))

        return self

    model_config = SettingsConfigDict(
        env_file=BACKEND_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
