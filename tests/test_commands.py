"""Tests for agent/commands.py"""

from pathlib import Path

import pytest

from agent.commands import CommandHandler
from code_engine.search import CodeSearchEngine
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
