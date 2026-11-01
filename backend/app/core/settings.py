"""Runtime settings, read from environment variables prefixed with MINDFUL_."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MINDFUL_", env_file=".env", extra="ignore")

    data_dir: Path = REPO_ROOT / "data" / "raw" / "MINDFUL_Data"
    processed_dir: Path = REPO_ROOT / "data" / "processed"
    upstream_dir: Path = REPO_ROOT / "references" / "upstream-mindful"
    frontend_origin: str = "http://localhost:3000"


@lru_cache
def get_settings() -> Settings:
    return Settings()
