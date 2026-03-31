import aiosqlite
import logging

logger = logging.getLogger(__name__)

SCHEMA_V1 = """
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    platform TEXT NOT NULL,
    username TEXT,
    display_name TEXT,
    is_authorized INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    chat_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    title TEXT NOT NULL,
    due_date TEXT,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agent_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    agent_name TEXT NOT NULL,
    input_summary TEXT,
    output_summary TEXT,
    tools_used TEXT,
    duration_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_conv_user ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conv_chat ON conversations(chat_id);
CREATE INDEX IF NOT EXISTS idx_tasks_user ON tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_notes_user ON notes(user_id);
CREATE INDEX IF NOT EXISTS idx_logs_user ON agent_logs(user_id);
"""


async def run_migrations(db: aiosqlite.Connection):
    """Run schema migrations. Drops old tables on first run for clean start."""
    # Check if we're on the old schema (chat_id based) or new (user_id based)
    cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'")
    has_version_table = await cursor.fetchone()

    if not has_version_table:
        # Check if old tables exist (from pre-migration codebase)
        cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'")
        old_tasks = await cursor.fetchone()

        if old_tasks:
            # Check if old schema uses chat_id (old) vs user_id (new)
            cursor = await db.execute("PRAGMA table_info(tasks)")
            columns = [row[1] for row in await cursor.fetchall()]
            if "chat_id" in columns and "user_id" not in columns:
                logger.info("Detected old schema — dropping and recreating tables...")
                await db.executescript("""
                    DROP TABLE IF EXISTS conversations;
                    DROP TABLE IF EXISTS tasks;
                    DROP TABLE IF EXISTS notes;
                """)

        # Create all tables fresh
        await db.executescript(SCHEMA_V1)

        # Create version tracking
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY
            );
            INSERT OR IGNORE INTO schema_version (version) VALUES (1);
        """)
        await db.commit()
        logger.info("Database schema v1 initialized.")
    else:
        # Already migrated — ensure tables exist (idempotent)
        await db.executescript(SCHEMA_V1)
        await db.commit()
        logger.info("Database schema up to date.")
