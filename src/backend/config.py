from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    NEWS_API_KEY: str = ""
    AZURE_OPENAI_KEY: str = ""
    AZURE_OPENAI_ENDPOINT: str = ""
    AZURE_OPENAI_DEPLOYMENT: str = "gpt-4o"
    DATABASE_URL: str = "sqlite:///./newsperspective.db"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
