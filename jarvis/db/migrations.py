"""
Database schema migrations. Versioned — each upgrade is additive.

v1: Original tables (users, conversations, tasks, notes, agent_logs)
v2: Full personal AI storage (contacts, thoughts, vault, memories,
    scheduled_jobs, tags, taggables + enhanced existing tables)
"""

import aiosqlite
import logging

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────
#  SCHEMA v1 — Foundation (already deployed)
# ─────────────────────────────────────────────────────────────────

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


# ─────────────────────────────────────────────────────────────────
#  SCHEMA v2 — Full personal AI storage
# ─────────────────────────────────────────────────────────────────

SCHEMA_V2 = """
-- Users: add timezone, language, preferences
ALTER TABLE users ADD COLUMN timezone TEXT DEFAULT 'UTC';
ALTER TABLE users ADD COLUMN language TEXT DEFAULT 'en';
ALTER TABLE users ADD COLUMN preferences TEXT DEFAULT '{}';

-- Tasks: add description, priority, category, due_time, recurrence
ALTER TABLE tasks ADD COLUMN description TEXT;
ALTER TABLE tasks ADD COLUMN priority TEXT DEFAULT 'medium';
ALTER TABLE tasks ADD COLUMN category TEXT;
ALTER TABLE tasks ADD COLUMN due_time TEXT;
ALTER TABLE tasks ADD COLUMN is_recurring INTEGER DEFAULT 0;
ALTER TABLE tasks ADD COLUMN recurrence_rule TEXT;

-- Notes: add category, is_pinned
ALTER TABLE notes ADD COLUMN category TEXT;
ALTER TABLE notes ADD COLUMN is_pinned INTEGER DEFAULT 0;

-- Conversations: add is_redacted flag
ALTER TABLE conversations ADD COLUMN is_redacted INTEGER DEFAULT 0;
"""

SCHEMA_V2_NEW_TABLES = """
-- ── CONTACTS ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    nickname TEXT,
    relationship TEXT,
    phone_enc TEXT,                      -- encrypted
    email_enc TEXT,                      -- encrypted
    address_enc TEXT,                    -- encrypted
    birthday TEXT,                       -- YYYY-MM-DD
    anniversary TEXT,                    -- YYYY-MM-DD
    context TEXT,                        -- free-text about this person
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_contacts_user ON contacts(user_id);
CREATE INDEX IF NOT EXISTS idx_contacts_name ON contacts(user_id, name);

-- ── THOUGHTS ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS thoughts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    content TEXT NOT NULL,
    thought_type TEXT DEFAULT 'random',  -- idea, opinion, fact, random, bookmark, quote, snippet, question
    mood TEXT,                           -- happy, frustrated, curious, excited, etc.
    source TEXT DEFAULT 'telegram',      -- which interface captured it
    is_pinned INTEGER DEFAULT 0,
    is_private INTEGER DEFAULT 0,        -- if 1, content is encrypted too
    linked_contact_id INTEGER,           -- FK to contacts.id (nullable)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (linked_contact_id) REFERENCES contacts(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_thoughts_user ON thoughts(user_id);
CREATE INDEX IF NOT EXISTS idx_thoughts_type ON thoughts(user_id, thought_type);

-- ── TAGS ──────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    color TEXT,                          -- hex: "#FF5733"
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, name)               -- one tag name per user
);
CREATE INDEX IF NOT EXISTS idx_tags_user ON tags(user_id);

-- ── TAGGABLES (junction: tag ↔ any entity) ────────────────────
CREATE TABLE IF NOT EXISTS taggables (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tag_id INTEGER NOT NULL,
    entity_type TEXT NOT NULL,           -- "thought", "note", "task", "contact"
    entity_id INTEGER NOT NULL,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE,
    UNIQUE(tag_id, entity_type, entity_id)
);
CREATE INDEX IF NOT EXISTS idx_taggables_entity ON taggables(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_taggables_tag ON taggables(tag_id);

-- ── VAULT (encrypted secrets) ─────────────────────────────────
CREATE TABLE IF NOT EXISTS vault (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    label TEXT NOT NULL,                 -- "Netflix password", "WiFi", "Bank PIN"
    value_enc TEXT NOT NULL,             -- ALWAYS encrypted
    category TEXT DEFAULT 'general',     -- password, pin, key, secret, personal
    notes TEXT,                          -- non-sensitive context
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_vault_user ON vault(user_id);
CREATE INDEX IF NOT EXISTS idx_vault_label ON vault(user_id, label);

-- ── MEMORIES (Jarvis's learned knowledge) ─────────────────────
CREATE TABLE IF NOT EXISTS memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    fact TEXT NOT NULL,                  -- "User prefers Python over Java"
    category TEXT DEFAULT 'fact',        -- preference, fact, opinion, habit, relationship
    confidence REAL DEFAULT 0.5,         -- 0.0 to 1.0
    source_conversation_id INTEGER,      -- FK to conversations.id
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_confirmed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_conversation_id) REFERENCES conversations(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_memories_user ON memories(user_id);
CREATE INDEX IF NOT EXISTS idx_memories_category ON memories(user_id, category);

-- ── SCHEDULED JOBS ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS scheduled_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    action_type TEXT NOT NULL,           -- send_message, reminder, recurring_task
    description TEXT,                    -- "Birthday wishes to Satyajit"
    payload TEXT DEFAULT '{}',           -- JSON blob
    target_contact_id INTEGER,           -- FK to contacts.id
    scheduled_at TEXT,                   -- ISO datetime
    recurrence_rule TEXT,                -- daily, weekly:mon, yearly:04-01
    status TEXT DEFAULT 'pending',       -- pending, completed, failed, cancelled
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    executed_at TIMESTAMP,
    FOREIGN KEY (target_contact_id) REFERENCES contacts(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_jobs_user ON scheduled_jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON scheduled_jobs(status, scheduled_at);
"""


# ─────────────────────────────────────────────────────────────────
#  MIGRATION RUNNER
# ─────────────────────────────────────────────────────────────────

async def _get_schema_version(db: aiosqlite.Connection) -> int:
    """Get current schema version, or 0 if no version table exists."""
    cursor = await db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
    )
    if not await cursor.fetchone():
        return 0
    cursor = await db.execute("SELECT MAX(version) FROM schema_version")
    row = await cursor.fetchone()
    return row[0] if row and row[0] else 0


async def _set_schema_version(db: aiosqlite.Connection, version: int):
    """Record that we've migrated to this version."""
    await db.execute(
        "CREATE TABLE IF NOT EXISTS schema_version (version INTEGER PRIMARY KEY)"
    )
    await db.execute(
        "INSERT OR REPLACE INTO schema_version (version) VALUES (?)", (version,)
    )


async def _migrate_to_v1(db: aiosqlite.Connection):
    """Create foundation tables."""
    # Check if old schema (chat_id based) exists and needs cleanup
    cursor = await db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'"
    )
    if await cursor.fetchone():
        cursor = await db.execute("PRAGMA table_info(tasks)")
        columns = [row[1] for row in await cursor.fetchall()]
        if "chat_id" in columns and "user_id" not in columns:
            logger.info("Detected old schema — dropping and recreating...")
            await db.executescript("""
                DROP TABLE IF EXISTS conversations;
                DROP TABLE IF EXISTS tasks;
                DROP TABLE IF EXISTS notes;
            """)

    await db.executescript(SCHEMA_V1)
    logger.info("Schema v1 applied — foundation tables.")


async def _migrate_to_v2(db: aiosqlite.Connection):
    """Add all new tables + enhance existing ones."""
    # ALTER TABLE statements must run one at a time (SQLite limitation)
    for line in SCHEMA_V2.strip().split("\n"):
        line = line.strip()
        if line and not line.startswith("--"):
            try:
                await db.execute(line)
            except Exception as e:
                # Column might already exist (re-running migration)
                if "duplicate column" not in str(e).lower():
                    logger.debug(f"ALTER skipped (likely exists): {e}")

    # New tables (idempotent with IF NOT EXISTS)
    await db.executescript(SCHEMA_V2_NEW_TABLES)
    logger.info("Schema v2 applied — contacts, thoughts, vault, memories, schedules, tags.")


# Migration registry: version → function
MIGRATIONS = {
    1: _migrate_to_v1,
    2: _migrate_to_v2,
}

LATEST_VERSION = max(MIGRATIONS.keys())


async def run_migrations(db: aiosqlite.Connection):
    """Run all pending migrations from current version to latest."""
    current = await _get_schema_version(db)
    logger.info(f"Current schema version: {current}, latest: {LATEST_VERSION}")

    if current >= LATEST_VERSION:
        logger.info("Database schema is up to date.")
        return

    for version in range(current + 1, LATEST_VERSION + 1):
        migrate_fn = MIGRATIONS[version]
        logger.info(f"Running migration v{version}...")
        await migrate_fn(db)
        await _set_schema_version(db, version)

    await db.commit()
    logger.info(f"Database migrated to v{LATEST_VERSION}.")
