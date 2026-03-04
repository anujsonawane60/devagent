"""Application settings loaded from environment variables."""

import os
from dataclasses import dataclass, field
from typing import List

from dotenv import load_dotenv


@dataclass
class Settings:
    telegram_bot_token: str = ""
    telegram_allowed_users: List[int] = field(default_factory=list)
    llm_provider: str = "anthropic"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-20250514"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    db_path: str = "devagent.db"
    debug: bool = False

    @classmethod
    def from_env(cls, env_path: str | None = None) -> "Settings":
        """Load settings from .env file and environment variables."""
        load_dotenv(env_path or ".env")

        allowed_users_str = os.getenv("TELEGRAM_ALLOWED_USERS", "")
        allowed_users = []
        if allowed_users_str.strip():
            allowed_users = [int(uid.strip()) for uid in allowed_users_str.split(",") if uid.strip()]

        return cls(
            telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
            telegram_allowed_users=allowed_users,
            llm_provider=os.getenv("LLM_PROVIDER", "anthropic").lower(),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
            anthropic_model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514"),
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4o"),
            db_path=os.getenv("DB_PATH", "devagent.db"),
            debug=os.getenv("DEBUG", "false").lower() in ("true", "1", "yes"),
        )

    def validate(self) -> List[str]:
        """Validate settings. Returns list of error messages (empty = valid)."""
        errors = []
        if not self.telegram_bot_token:
            errors.append("TELEGRAM_BOT_TOKEN is required")
        if self.llm_provider not in ("anthropic", "openai"):
            errors.append(f"LLM_PROVIDER must be 'anthropic' or 'openai', got '{self.llm_provider}'")
        if self.llm_provider == "anthropic" and not self.anthropic_api_key:
            errors.append("ANTHROPIC_API_KEY is required when LLM_PROVIDER is 'anthropic'")
        if self.llm_provider == "openai" and not self.openai_api_key:
            errors.append("OPENAI_API_KEY is required when LLM_PROVIDER is 'openai'")
        return errors
