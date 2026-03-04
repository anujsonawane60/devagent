"""Shared fixtures for tests."""

from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from code_engine.analyzer import ProjectAnalyzer
from code_engine.parser import CodeParser
from code_engine.search import CodeSearchEngine
from agent.commands import CommandHandler
from agent.context import ContextBuilder
from config.llm import LLMProvider, LLMResponse
from storage.db import Database
from tg_bot.auth import AuthManager

DUMMY_DATA_DIR = Path(__file__).parent / "dummy_data"


@pytest.fixture
def settings():
    from config.settings import Settings
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


@pytest.fixture
def parser():
    return CodeParser()


@pytest.fixture
async def db(tmp_path):
    database = Database(str(tmp_path / "test.db"))
    await database.connect()
    yield database
    await database.close()


@pytest.fixture
async def search_engine(db):
    return CodeSearchEngine(db)


@pytest.fixture
async def context_builder(search_engine):
    return ContextBuilder(search_engine)


@pytest.fixture
def git_repo(tmp_path):
    """Create a temporary git repo for testing."""
    import git
    repo = git.Repo.init(str(tmp_path))
    repo.config_writer().set_value("user", "name", "Test User").release()
    repo.config_writer().set_value("user", "email", "test@example.com").release()
    return tmp_path, repo


@pytest.fixture
def mock_llm():
    """Create a mock LLM provider."""
    llm = AsyncMock(spec=LLMProvider)
    llm.provider_name.return_value = "mock"
    llm.generate.return_value = LLMResponse(
        content='{"changes": [], "summary": "No changes"}',
        model="mock-model",
        usage={"input_tokens": 10, "output_tokens": 20},
    )
    return llm
