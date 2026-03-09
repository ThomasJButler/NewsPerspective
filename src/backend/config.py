from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    DATABASE_URL: str = "sqlite:///./newsperspective.db"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
