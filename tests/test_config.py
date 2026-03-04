"""Tests for config/settings.py"""

import os
from unittest.mock import patch

from config.settings import Settings


class TestSettingsFromEnv:
    def test_loads_defaults(self):
        with patch.dict(os.environ, {}, clear=True):
            s = Settings.from_env(env_path="/dev/null")
        assert s.llm_provider == "anthropic"
        assert s.debug is False
        assert s.db_path == "devagent.db"

    def test_loads_telegram_token(self):
        with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "tok123"}, clear=True):
            s = Settings.from_env(env_path="/dev/null")
        assert s.telegram_bot_token == "tok123"

    def test_loads_allowed_users(self):
        with patch.dict(os.environ, {"TELEGRAM_ALLOWED_USERS": "111,222,333"}, clear=True):
            s = Settings.from_env(env_path="/dev/null")
        assert s.telegram_allowed_users == [111, 222, 333]

    def test_empty_allowed_users(self):
        with patch.dict(os.environ, {"TELEGRAM_ALLOWED_USERS": ""}, clear=True):
            s = Settings.from_env(env_path="/dev/null")
        assert s.telegram_allowed_users == []

    def test_loads_debug_true(self):
        with patch.dict(os.environ, {"DEBUG": "true"}, clear=True):
            s = Settings.from_env(env_path="/dev/null")
        assert s.debug is True

    def test_loads_llm_provider_openai(self):
        with patch.dict(os.environ, {"LLM_PROVIDER": "OpenAI"}, clear=True):
            s = Settings.from_env(env_path="/dev/null")
        assert s.llm_provider == "openai"


class TestSettingsValidation:
    def test_valid_anthropic_config(self):
        s = Settings(
            telegram_bot_token="tok",
            llm_provider="anthropic",
            anthropic_api_key="key",
        )
        assert s.validate() == []

    def test_missing_token_and_key(self):
        s = Settings(llm_provider="anthropic")
        errors = s.validate()
        assert "TELEGRAM_BOT_TOKEN is required" in errors
        assert "ANTHROPIC_API_KEY is required when LLM_PROVIDER is 'anthropic'" in errors


class TestIntegrationSettings:
    def test_default_integration_settings(self):
        s = Settings()
        assert s.github_token == ""
        assert s.sentry_auth_token == ""
        assert s.sentry_org == ""
        assert s.sentry_project == ""
        assert s.vercel_token == ""
        assert s.vercel_project_id == ""
        assert s.chromadb_path == "devagent_chroma"

    def test_loads_integration_env_vars(self):
        env = {
            "GITHUB_TOKEN": "gh_token",
            "SENTRY_AUTH_TOKEN": "sentry_tok",
            "SENTRY_ORG": "my-org",
            "SENTRY_PROJECT": "my-proj",
            "VERCEL_TOKEN": "vrc_tok",
            "VERCEL_PROJECT_ID": "prj_123",
            "VERCEL_TEAM_ID": "team_456",
            "CHROMADB_PATH": "/data/chroma",
        }
        with patch.dict(os.environ, env, clear=True):
            s = Settings.from_env(env_path="/dev/null")
        assert s.github_token == "gh_token"
        assert s.sentry_auth_token == "sentry_tok"
        assert s.sentry_org == "my-org"
        assert s.sentry_project == "my-proj"
        assert s.vercel_token == "vrc_tok"
        assert s.vercel_project_id == "prj_123"
        assert s.vercel_team_id == "team_456"
        assert s.chromadb_path == "/data/chroma"
