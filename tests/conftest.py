"""Shared fixtures for tests."""

from pathlib import Path

import pytest

from code_engine.analyzer import ProjectAnalyzer
from agent.commands import CommandHandler
from config.settings import Settings
from tg_bot.auth import AuthManager

DUMMY_DATA_DIR = Path(__file__).parent / "dummy_data"


@pytest.fixture
def settings():
    return Settings(
        telegram_bot_token="test-token",
        telegram_allowed_users=[111, 222],
        llm_provider="anthropic",
        anthropic_api_key="test-key",
    )


@pytest.fixture
def auth_manager():
    return AuthManager([111, 222])


@pytest.fixture
def analyzer():
    return ProjectAnalyzer()


@pytest.fixture
def command_handler(analyzer):
    return CommandHandler(analyzer=analyzer)


@pytest.fixture
def dummy_data_dir():
    return DUMMY_DATA_DIR
