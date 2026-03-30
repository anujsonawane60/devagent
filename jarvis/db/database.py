import aiosqlite
import os
from pathlib import Path

from jarvis.config import settings

DB_PATH = settings.DATABASE_PATH


async def get_db() -> aiosqlite.Connection:
    os.makedirs(Path(DB_PATH).parent, exist_ok=True)
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode=WAL")
    return db


async def init_db():
    db = await get_db()
    try:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT NOT NULL,
                title TEXT NOT NULL,
                due_date TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_conv_chat ON conversations(chat_id);
            CREATE INDEX IF NOT EXISTS idx_tasks_chat ON tasks(chat_id);
            CREATE INDEX IF NOT EXISTS idx_notes_chat ON notes(chat_id);
        """)
        await db.commit()
    finally:
        await db.close()
