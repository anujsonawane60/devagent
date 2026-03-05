"""Application settings loaded from environment variables."""

import os
from dataclasses import dataclass, field
from typing import List

from dotenv import load_dotenv


SUPPORTED_PROVIDERS = ("anthropic", "openai", "gemini", "deepseek")


@dataclass
class Settings:
    telegram_bot_token: str = ""
    telegram_allowed_users: List[int] = field(default_factory=list)
    llm_provider: str = "anthropic"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-20250514"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    deepseek_api_key: str = ""
    deepseek_model: str = "deepseek-chat"
    db_path: str = "devagent.db"
    chromadb_path: str = "devagent_chroma"
    github_token: str = ""
    sentry_auth_token: str = ""
    sentry_org: str = ""
    sentry_project: str = ""
    vercel_token: str = ""
    vercel_project_id: str = ""
    vercel_team_id: str = ""
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
            gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
            gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
            deepseek_api_key=os.getenv("DEEPSEEK_API_KEY", ""),
            deepseek_model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            db_path=os.getenv("DB_PATH", "devagent.db"),
            chromadb_path=os.getenv("CHROMADB_PATH", "devagent_chroma"),
            github_token=os.getenv("GITHUB_TOKEN", ""),
            sentry_auth_token=os.getenv("SENTRY_AUTH_TOKEN", ""),
            sentry_org=os.getenv("SENTRY_ORG", ""),
            sentry_project=os.getenv("SENTRY_PROJECT", ""),
            vercel_token=os.getenv("VERCEL_TOKEN", ""),
            vercel_project_id=os.getenv("VERCEL_PROJECT_ID", ""),
            vercel_team_id=os.getenv("VERCEL_TEAM_ID", ""),
            debug=os.getenv("DEBUG", "false").lower() in ("true", "1", "yes"),
        )

    def get_llm_api_key(self) -> str:
        """Get the API key for the configured LLM provider."""
        return {
            "anthropic": self.anthropic_api_key,
            "openai": self.openai_api_key,
            "gemini": self.gemini_api_key,
            "deepseek": self.deepseek_api_key,
        }.get(self.llm_provider, "")

    def get_llm_model(self) -> str:
        """Get the model name for the configured LLM provider."""
        return {
            "anthropic": self.anthropic_model,
            "openai": self.openai_model,
            "gemini": self.gemini_model,
            "deepseek": self.deepseek_model,
        }.get(self.llm_provider, "")

    def validate(self) -> List[str]:
        """Validate settings. Returns list of error messages (empty = valid)."""
        errors = []
        if not self.telegram_bot_token:
            errors.append("TELEGRAM_BOT_TOKEN is required")
        if self.llm_provider not in SUPPORTED_PROVIDERS:
            errors.append(f"LLM_PROVIDER must be one of {SUPPORTED_PROVIDERS}, got '{self.llm_provider}'")
        elif not self.get_llm_api_key():
            key_name = f"{self.llm_provider.upper()}_API_KEY"
            errors.append(f"{key_name} is required when LLM_PROVIDER is '{self.llm_provider}'")
        return errors
