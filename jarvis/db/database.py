import aiosqlite
import os
from pathlib import Path

from jarvis.config import settings


class Database:
    """Singleton async SQLite connection pool."""

    _db: aiosqlite.Connection | None = None

    @classmethod
    async def get(cls) -> aiosqlite.Connection:
        if cls._db is None:
            os.makedirs(Path(settings.DATABASE_PATH).parent, exist_ok=True)
            cls._db = await aiosqlite.connect(settings.DATABASE_PATH)
            cls._db.row_factory = aiosqlite.Row
            await cls._db.execute("PRAGMA journal_mode=WAL")
        return cls._db

    @classmethod
    async def close(cls):
        if cls._db is not None:
            await cls._db.close()
            cls._db = None


async def get_db() -> aiosqlite.Connection:
    """Convenience shortcut."""
    return await Database.get()


async def init_db():
    """Initialize database schema and run migrations."""
    from jarvis.db.migrations import run_migrations

    db = await get_db()
    await run_migrations(db)
