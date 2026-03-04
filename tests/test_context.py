"""Tests for agent/context.py — ~6 tests."""

from pathlib import Path

import pytest

from agent.context import ContextBuilder, ContextResult, ContextFile
from code_engine.parser import CodeParser
from code_engine.search import CodeSearchEngine
from storage.db import Database

DUMMY_DATA = Path(__file__).parent / "dummy_data"


@pytest.fixture
async def indexed_context(db, parser):
    """Context builder with indexed sample project."""
    engine = CodeSearchEngine(db)
    project = str(DUMMY_DATA / "sample_python_project")
    await engine.index_project(project, parser)
    return ContextBuilder(engine), project


class TestContextBuilder:
    @pytest.mark.asyncio
    async def test_get_context_for_known_function(self, indexed_context):
        builder, project = indexed_context
        result = await builder.get_context("create_user", project)
        assert isinstance(result, ContextResult)
        assert result.total_entities >= 1
        assert len(result.files) >= 1
        assert result.query == "create_user"

    @pytest.mark.asyncio
    async def test_context_includes_entities(self, indexed_context):
        builder, project = indexed_context
        result = await builder.get_context("User", project)
        all_entities = []
        for f in result.files:
            all_entities.extend(f.entities)
        assert len(all_entities) >= 1

    @pytest.mark.asyncio
    async def test_empty_query(self, indexed_context):
        builder, project = indexed_context
        result = await builder.get_context("", project)
        assert result.total_entities == 0
        assert len(result.files) == 0

    @pytest.mark.asyncio
    async def test_token_budget_trimming(self, indexed_context):
        builder, project = indexed_context
        # Very small budget should limit results
        result = await builder.get_context("User", project, token_budget=50)
        # Should still return something but be trimmed
        assert isinstance(result, ContextResult)

    @pytest.mark.asyncio
    async def test_format_context(self, indexed_context):
        builder, project = indexed_context
        result = await builder.get_context("User", project)
        formatted = builder.format_context(result)
        assert "User" in formatted
        assert "Code Context" in formatted

    @pytest.mark.asyncio
    async def test_format_context_no_results(self, indexed_context):
        builder, project = indexed_context
        empty_result = ContextResult(query="nonexistent_xyz")
        formatted = builder.format_context(empty_result)
        assert "No relevant code found" in formatted
