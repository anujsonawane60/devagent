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
