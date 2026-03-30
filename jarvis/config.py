from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o"
    TELEGRAM_BOT_TOKEN: str
    DATABASE_PATH: str = str(Path(__file__).parent.parent / "data" / "jarvis.db")
    WEBHOOK_URL: str = ""  # Leave empty for polling mode (local dev)
    MEMORY_WINDOW: int = 20  # Number of recent messages to include in context
    LOG_LEVEL: str = "INFO"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
