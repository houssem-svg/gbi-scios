from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parents[2]

# Known insecure placeholder JWT secrets that MUST NOT be used in production.
_INSECURE_JWT_PLACEHOLDERS = {
    "change-me-to-a-long-random-production-secret",
    "change-me",
    "secret",
    "changeme",
    "supersecret",
    "your-secret-key",
    "replace-with-a-strong-64-char-secret-run-secrets-token-urlsafe-64",
}


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

    jwt_secret_key: str = Field(..., validation_alias="JWT_SECRET_KEY", min_length=32)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # CORS allow-list, comma-separated. Defaults to local dev origins only.
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    # LCP payroll recognition factor: 53.4% of Saudi payroll counts as local content.
    # The remaining 46.6% is treated as payroll value leakage outside the Kingdom.
    saudi_payroll_recognition_factor: float = 0.534

    # Data sovereignty: when set to "in-kingdom", the app will refuse to start if the
    # database URL does not resolve to a host allow-listed for Saudi residency.
    data_residency: str = "in-kingdom"
    saudi_db_host_allowlist: str = "localhost,127.0.0.1,postgres,db,.saudi.cloud,.saudicloud.com,.local"

    @field_validator("jwt_secret_key")
    @classmethod
    def _validate_jwt_secret(cls, v: str) -> str:
        if v in _INSECURE_JWT_PLACEHOLDERS:
            raise ValueError(
                "JWT_SECRET_KEY is set to a known insecure placeholder. "
                "Generate a strong key, e.g. via: python -c \"import secrets; print(secrets.token_urlsafe(64))\""
            )
        if len(v) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters long.")
        return v

    @field_validator("saudi_payroll_recognition_factor")
    @classmethod
    def _validate_payroll_factor(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("saudi_payroll_recognition_factor must be between 0.0 and 1.0")
        return v

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @field_validator("data_residency")
    @classmethod
    def _validate_data_residency(cls, v: str) -> str:
        allowed = {"in-kingdom", "off"}
        if v not in allowed:
            raise ValueError("data_residency must be 'in-kingdom' or 'off'")
        return v

    @model_validator(mode="after")
    def normalize_local_paths(self) -> "Settings":
        if self.database_url.startswith("sqlite:///./"):
            db_path = BACKEND_ROOT / self.database_url.removeprefix("sqlite:///./")
            self.database_url = f"sqlite:///{db_path.as_posix()}"
        elif self.database_url.startswith("sqlite:///") and not self.database_url.startswith("sqlite:////"):
            # also normalize sqlite:///relative.db
            rest = self.database_url.removeprefix("sqlite:///")
            if not Path(rest).is_absolute():
                db_path = BACKEND_ROOT / rest
                self.database_url = f"sqlite:///{db_path.as_posix()}"

        for field_name in ("upload_storage_dir", "parsing_log_dir", "compliance_scan_log_dir"):
            value = getattr(self, field_name)
            path = Path(value)
            if not path.is_absolute():
                setattr(self, field_name, str(BACKEND_ROOT / path))

        # Data sovereignty guard: refuse to run if DB host is not in the Saudi allow-list.
        if self.data_residency == "in-kingdom" and not self.database_url.startswith("sqlite"):
            host = _extract_db_host(self.database_url)
            if host and not _host_allowed(host, self.saudi_db_host_allowlist):
                raise ValueError(
                    f"Data sovereignty violation: database host '{host}' is not in the Saudi "
                    f"residency allow-list. Set data_residency='off' only for explicit non-production "
                    f"override, or use a Saudi-resident database provider."
                )

        return self

    model_config = SettingsConfigDict(
        env_file=BACKEND_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


def _extract_db_host(url: str) -> str | None:
    """Extract the host from a postgres/mysql style URL. Returns None if not parseable."""
    # postgresql+psycopg://user:pass@host:port/db
    if "@" in url and "://" in url:
        after_at = url.split("@", 1)[1]
        host_port = after_at.split("/", 1)[0]
        return host_port.split(":", 1)[0]
    return None


def _host_allowed(host: str, allowlist_csv: str) -> bool:
    host_lc = host.lower().strip()
    for token in allowlist_csv.split(","):
        token = token.strip().lower()
        if not token:
            continue
        if host_lc == token or host_lc.endswith(token):
            return True
    return False


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
