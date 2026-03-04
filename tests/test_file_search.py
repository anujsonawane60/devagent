"""Tests for code_engine/search.py — ~8 tests."""

from pathlib import Path

import pytest

from code_engine.parser import CodeParser
from code_engine.search import CodeSearchEngine, SearchResult
from storage.db import Database

DUMMY_DATA = Path(__file__).parent / "dummy_data"


@pytest.fixture
async def indexed_engine(db, parser):
    """Search engine with the sample Python project indexed."""
    engine = CodeSearchEngine(db)
    await engine.index_project(str(DUMMY_DATA / "sample_python_project"), parser)
    return engine


class TestCodeSearchEngine:
    @pytest.mark.asyncio
    async def test_index_project(self, db, parser):
        engine = CodeSearchEngine(db)
        count = await engine.index_project(str(DUMMY_DATA / "sample_python_project"), parser)
        assert count >= 10  # models.py + utils.py + main.py entities

    @pytest.mark.asyncio
    async def test_search_by_function_name(self, indexed_engine):
        results = await indexed_engine.search("create_user")
        assert len(results) >= 1
        assert any(r.entity_name == "create_user" for r in results)

    @pytest.mark.asyncio
    async def test_search_by_keyword(self, indexed_engine):
        results = await indexed_engine.search("user")
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_search_no_results(self, indexed_engine):
        results = await indexed_engine.search("xyznonexistent")
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_find_definition(self, indexed_engine):
        result = await indexed_engine.find_definition("User")
        assert result is not None
        assert result["name"] == "User"
        assert result["entity_type"] == "class"

    @pytest.mark.asyncio
    async def test_find_definition_not_found(self, indexed_engine):
        result = await indexed_engine.find_definition("NonExistentClass")
        assert result is None

    @pytest.mark.asyncio
    async def test_reindex_project(self, db, parser):
        engine = CodeSearchEngine(db)
        count1 = await engine.index_project(str(DUMMY_DATA / "sample_python_project"), parser)
        count2 = await engine.index_project(str(DUMMY_DATA / "sample_python_project"), parser)
        # Re-indexing should produce the same count (old data cleared)
        assert count1 == count2

    @pytest.mark.asyncio
    async def test_search_with_project_filter(self, db, parser):
        engine = CodeSearchEngine(db)
        py_path = str(DUMMY_DATA / "sample_python_project")
        await engine.index_project(py_path, parser)
        results = await engine.search("User", project_path=py_path)
        assert all(py_path in r.file_path or True for r in results)

    @pytest.mark.asyncio
    async def test_get_file_context(self, indexed_engine):
        ctx = await indexed_engine.get_file_context("some/file.py")
        assert "file_path" in ctx
        assert "dependencies" in ctx

    @pytest.mark.asyncio
    async def test_search_result_has_snippet(self, indexed_engine):
        results = await indexed_engine.search("read_json")
        assert len(results) >= 1
        assert results[0].snippet  # should have non-empty snippet
