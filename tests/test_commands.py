"""Tests for agent/commands.py"""

import json
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from agent.commands import CommandHandler
from code_engine.search import CodeSearchEngine
from config.llm import LLMProvider, LLMResponse
from storage.db import Database

DUMMY_DATA = Path(__file__).parent / "dummy_data"


class TestCommandHandler:
    def test_help(self, command_handler):
        result = command_handler.help()
        assert "/help" in result
        assert "/status" in result
        assert "/analyze" in result
        assert "/search" in result
        assert "/index" in result
        assert "/find" in result
        assert "/generate" in result
        assert "/diff" in result

    def test_status(self, command_handler):
        result = command_handler.status()
        assert "running" in result.lower()

    def test_analyze_valid_project(self, command_handler):
        result = command_handler.analyze(str(DUMMY_DATA / "sample_nextjs_project"))
        assert "nextjs" in result.lower() or "typescript" in result.lower()

    def test_analyze_empty_path(self, command_handler):
        result = command_handler.analyze("")
        assert "Usage" in result

    def test_analyze_nonexistent(self, command_handler):
        result = command_handler.analyze("/nonexistent/path")
        assert "Could not detect" in result


class TestCommandHandlerAsync:
    @pytest.mark.asyncio
    async def test_index_project(self, db):
        handler = CommandHandler(db=db)
        result = await handler.index(str(DUMMY_DATA / "sample_python_project"))
        assert "Indexed" in result
        assert "entities" in result

    @pytest.mark.asyncio
    async def test_index_empty_path(self, db):
        handler = CommandHandler(db=db)
        result = await handler.index("")
        assert "Usage" in result

    @pytest.mark.asyncio
    async def test_search_no_db(self):
        handler = CommandHandler()
        result = await handler.search("test")
        assert "not available" in result.lower()

    @pytest.mark.asyncio
    async def test_search_after_index(self, db):
        handler = CommandHandler(db=db)
        await handler.index(str(DUMMY_DATA / "sample_python_project"))
        result = await handler.search("User")
        assert "User" in result

    @pytest.mark.asyncio
    async def test_find_after_index(self, db):
        handler = CommandHandler(db=db)
        await handler.index(str(DUMMY_DATA / "sample_python_project"))
        result = await handler.find("User")
        assert "Found" in result

    @pytest.mark.asyncio
    async def test_find_empty(self, db):
        handler = CommandHandler(db=db)
        result = await handler.find("")
        assert "Usage" in result


class TestGenerateAndDiff:
    @pytest.mark.asyncio
    async def test_generate_no_llm(self):
        handler = CommandHandler()
        result = await handler.generate("add login", "/some/path")
        assert "not configured" in result.lower()

    @pytest.mark.asyncio
    async def test_generate_empty_task(self, mock_llm):
        handler = CommandHandler(llm=mock_llm)
        result = await handler.generate("", "/some/path")
        assert "Usage" in result

    @pytest.mark.asyncio
    async def test_generate_with_llm(self, mock_llm, tmp_path):
        mock_llm.generate.return_value = LLMResponse(
            content=json.dumps({
                "changes": [
                    {"file_path": "app.py", "action": "create", "content": "print(1)", "description": "main"}
                ],
                "summary": "done"
            }),
            model="mock",
            usage={"input_tokens": 5, "output_tokens": 10},
        )
        handler = CommandHandler(llm=mock_llm)
        result = await handler.generate("add main", str(tmp_path))
        assert "1 change" in result
        assert "app.py" in result

    def test_diff_empty_path(self):
        handler = CommandHandler()
        result = handler.diff("")
        assert "Usage" in result

    def test_diff_invalid_repo(self, tmp_path):
        handler = CommandHandler()
        result = handler.diff(str(tmp_path))
        assert "Git error" in result

    def test_diff_clean_repo(self, git_repo):
        tmp_path, repo = git_repo
        (tmp_path / "f.txt").write_text("hi")
        repo.index.add(["f.txt"])
        repo.index.commit("init")
        handler = CommandHandler()
        result = handler.diff(str(tmp_path))
        assert "No unstaged changes" in result


class TestNewCommands:
    def test_help_includes_new_commands(self, command_handler):
        result = command_handler.help()
        assert "/add" in result
        assert "/fix" in result
        assert "/deploy" in result
        assert "/errors" in result
        assert "/pr" in result
        assert "/setup" in result

    def test_status_shows_integrations(self):
        from unittest.mock import MagicMock
        handler = CommandHandler(
            llm=MagicMock(),
            github=MagicMock(),
            sentry=MagicMock(),
            vercel=MagicMock(),
        )
        result = handler.status()
        assert "LLM" in result
        assert "GitHub" in result
        assert "Sentry" in result
        assert "Vercel" in result

    @pytest.mark.asyncio
    async def test_add_feature_no_llm(self):
        handler = CommandHandler()
        result = await handler.add_feature("user dashboard", "/some/path")
        assert "not configured" in result.lower()

    @pytest.mark.asyncio
    async def test_add_feature_empty_desc(self):
        handler = CommandHandler()
        result = await handler.add_feature("", "/some/path")
        assert "Usage" in result

    @pytest.mark.asyncio
    async def test_fix_error_no_sentry(self):
        handler = CommandHandler()
        result = await handler.fix_error("123", "/some/path")
        assert "Sentry not configured" in result

    @pytest.mark.asyncio
    async def test_deploy_no_vercel(self):
        handler = CommandHandler()
        result = await handler.deploy("staging", "")
        assert "Vercel not configured" in result

    @pytest.mark.asyncio
    async def test_deploy_empty_env(self):
        from unittest.mock import MagicMock
        handler = CommandHandler(vercel=MagicMock())
        result = await handler.deploy("", "")
        assert "Usage" in result

    @pytest.mark.asyncio
    async def test_deploy_invalid_env(self):
        from unittest.mock import MagicMock
        handler = CommandHandler(vercel=MagicMock())
        result = await handler.deploy("invalid", "")
        assert "must be" in result.lower()

    @pytest.mark.asyncio
    async def test_errors_no_sentry(self):
        handler = CommandHandler()
        result = await handler.errors()
        assert "Sentry not configured" in result

    @pytest.mark.asyncio
    async def test_create_pr_no_github(self):
        handler = CommandHandler()
        result = await handler.create_pr("Test PR", "")
        assert "GitHub not configured" in result

    @pytest.mark.asyncio
    async def test_create_pr_empty_title(self):
        from unittest.mock import MagicMock
        handler = CommandHandler(github=MagicMock())
        result = await handler.create_pr("", "")
        assert "Usage" in result

    @pytest.mark.asyncio
    async def test_setup_empty_path(self):
        handler = CommandHandler()
        result = await handler.setup_project("")
        assert "Usage" in result

    @pytest.mark.asyncio
    async def test_setup_nonexistent_path(self):
        handler = CommandHandler()
        result = await handler.setup_project("/nonexistent/xyz")
        assert "not found" in result.lower()

    @pytest.mark.asyncio
    async def test_setup_valid_project(self, tmp_path):
        # Create a basic Python project
        (tmp_path / "pyproject.toml").write_text("[tool.pytest]\n")
        (tmp_path / "main.py").write_text("print('hello')")
        handler = CommandHandler()
        result = await handler.setup_project(str(tmp_path))
        assert "Setting up" in result
        assert "Ready!" in result
