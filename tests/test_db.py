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
