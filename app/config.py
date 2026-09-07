from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parent.parent


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


settings = Settings()
