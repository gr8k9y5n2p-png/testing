from __future__ import annotations

import os
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parent.parent

# Website beta + local Next/FastAPI. Extra Vercel previews match CORS_ORIGIN_REGEX.
DEFAULT_CORS_ORIGINS = ",".join(
    [
        "https://testing-seven-umber-19.vercel.app",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]
)
DEFAULT_CORS_ORIGIN_REGEX = r"https://([a-z0-9-]+\.)*vercel\.app"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "sqlite:///./data/distributions.db"
    fetch_mode: str = "fixture"
    refresh_mode: str = "auto"
    fixtures_dir: Path = ROOT_DIR / "fixtures"
    http_timeout_seconds: float = 30.0
    http_user_agent: str = (
        "FundDistributionIngest/1.0 (+https://github.com; research/demo; contact ops)"
    )
    cors_origins: str = DEFAULT_CORS_ORIGINS
    cors_origin_regex: str = DEFAULT_CORS_ORIGIN_REGEX
    seed_on_start: bool = False

    @field_validator("database_url")
    @classmethod
    def _vercel_ephemeral_sqlite(cls, value: str) -> str:
        if os.getenv("VERCEL") and value.startswith("sqlite:///./"):
            return "sqlite:////tmp/distributions.db"
        return value


settings = Settings()
