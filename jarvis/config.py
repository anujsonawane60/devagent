from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from pathlib import Path


class Settings(BaseSettings):
    # --- LLM Defaults ---
    DEFAULT_LLM_PROVIDER: str = "openai"
    DEFAULT_LLM_MODEL: str = "gpt-4o"
    DEFAULT_LLM_TEMPERATURE: float = 0.7

    # --- API Keys (one per provider, optional except your default) ---
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""

    # --- Per-agent LLM overrides ---
    # JSON in env, e.g.: {"research_agent": {"provider": "anthropic", "model": "claude-sonnet-4-20250514"}}
    AGENT_LLM_OVERRIDES: dict = Field(default_factory=dict)

    # --- Telegram ---
    TELEGRAM_BOT_TOKEN: str = ""
    # JSON list of allowed Telegram user IDs. Empty = allow all (dev mode).
    TELEGRAM_ALLOWED_USERS: list[str] = Field(default_factory=list)

    @field_validator("TELEGRAM_ALLOWED_USERS", mode="before")
    @classmethod
    def _coerce_user_ids_to_str(cls, v):
        if isinstance(v, list):
            return [str(x) for x in v]
        return v

    # --- Encryption ---
    ENCRYPTION_KEY: str = ""  # Fernet key for encrypting sensitive data. Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

    # --- Vector Search ---
    VECTOR_DB_ENABLED: bool = True
    VECTOR_DB_PATH: str = str(Path(__file__).parent.parent / "data" / "vectors")
    EMBEDDING_PROVIDER: str = "openai"  # "openai" or "ollama"
    EMBEDDING_MODEL: str = "text-embedding-3-small"  # or "nomic-embed-text" for Ollama

    # --- Database ---
    DATABASE_PATH: str = str(Path(__file__).parent.parent / "data" / "jarvis.db")

    # --- Memory ---
    MEMORY_WINDOW: int = 20

    # --- Webhook (empty = polling mode for local dev) ---
    WEBHOOK_URL: str = ""

    # --- Logging ---
    LOG_LEVEL: str = "INFO"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
