"""Tests for storage/db.py"""

import pytest

from storage.db import Database


@pytest.fixture
async def db(tmp_path):
    database = Database(str(tmp_path / "test.db"))
    await database.connect()
    yield database
    await database.close()


class TestDatabase:
    @pytest.mark.asyncio
    async def test_connect(self, db):
        assert db._db is not None

    @pytest.mark.asyncio
    async def test_log_command(self, db):
        await db.log_command(123, "/help", "", "Help text")
        history = await db.get_command_history(123)
        assert len(history) == 1
        assert history[0]["command"] == "/help"

    @pytest.mark.asyncio
    async def test_command_history_limit(self, db):
        for i in range(5):
            await db.log_command(123, f"/cmd{i}")
        history = await db.get_command_history(123, limit=3)
        assert len(history) == 3

    @pytest.mark.asyncio
    async def test_save_and_get_manifest(self, db):
        manifest = {"language": "python", "framework": "fastapi"}
        await db.save_manifest("/path/to/project", manifest)
        result = await db.get_manifest("/path/to/project")
        assert result == manifest
        assert db.get_manifest is not None


class TestCodeEntities:
    @pytest.mark.asyncio
    async def test_save_and_search_entities(self, db):
        entities = [
            {
                "file_path": "app/models.py",
                "entity_type": "class",
                "name": "User",
                "line_start": 1,
                "line_end": 10,
                "signature": "class User",
                "docstring": "A user model",
            },
            {
                "file_path": "app/models.py",
                "entity_type": "function",
                "name": "create_user",
                "line_start": 12,
                "line_end": 15,
                "signature": "def create_user(name)",
                "docstring": "Create a new user",
            },
        ]
        await db.save_entities("/project", entities)
        results = await db.search_code("User", project_path="/project")
        assert len(results) >= 1
        assert any(r["name"] == "User" for r in results)

    @pytest.mark.asyncio
    async def test_search_no_results(self, db):
        results = await db.search_code("nonexistent_xyz")
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_clear_project_index(self, db):
        entities = [
            {
                "file_path": "test.py",
                "entity_type": "function",
                "name": "foo",
                "line_start": 1,
                "line_end": 3,
                "signature": "def foo()",
                "docstring": "",
            }
        ]
        await db.save_entities("/project", entities)
        await db.clear_project_index("/project")
        results = await db.search_code("foo", project_path="/project")
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_save_and_get_dependencies(self, db):
        deps = [
            {"source_file": "a.py", "target_file": "b.py", "import_name": "import b"},
            {"source_file": "c.py", "target_file": "a.py", "import_name": "import a"},
        ]
        await db.save_dependencies("/project", deps)
        related = await db.get_dependencies("a.py")
        assert "b.py" in related
        assert "c.py" in related
