from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _default_database_url() -> str:
    return f"sqlite:///{_repo_root() / 'newsperspective.db'}"


class Settings(BaseSettings):
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    DATABASE_URL: str = _default_database_url()

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def _normalize_database_url(cls, value: str) -> str:
        prefix = "sqlite:///"
        if isinstance(value, str) and value.startswith(prefix):
            relative_path = value[len(prefix) :]
            if relative_path.startswith("./") or relative_path.startswith("../"):
                return f"sqlite:///{(_repo_root() / relative_path).resolve()}"
        return value

    model_config = SettingsConfigDict(
        env_file=str(_repo_root() / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
