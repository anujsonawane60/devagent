"""SQLite storage via aiosqlite."""

import json
from datetime import datetime

import aiosqlite


class Database:
    def __init__(self, db_path: str = "devagent.db"):
        self.db_path = db_path
        self._db: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        self._db = await aiosqlite.connect(self.db_path)
        await self._db.execute("PRAGMA journal_mode=WAL")
        await self._create_tables()

    async def close(self) -> None:
        if self._db:
            await self._db.close()
            self._db = None

    async def _create_tables(self) -> None:
        await self._db.execute("""
            CREATE TABLE IF NOT EXISTS command_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                command TEXT NOT NULL,
                args TEXT,
                response TEXT,
                created_at TEXT NOT NULL
            )
        """)
        await self._db.execute("""
            CREATE TABLE IF NOT EXISTS project_manifest (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_path TEXT NOT NULL UNIQUE,
                manifest_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        await self._db.commit()

    async def log_command(self, user_id: int, command: str, args: str = "", response: str = "") -> None:
        await self._db.execute(
            "INSERT INTO command_log (user_id, command, args, response, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, command, args, response, datetime.utcnow().isoformat()),
        )
        await self._db.commit()

    async def get_command_history(self, user_id: int, limit: int = 10) -> list[dict]:
        cursor = await self._db.execute(
            "SELECT command, args, response, created_at FROM command_log WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        )
        rows = await cursor.fetchall()
        return [{"command": r[0], "args": r[1], "response": r[2], "created_at": r[3]} for r in rows]

    async def save_manifest(self, project_path: str, manifest: dict) -> None:
        await self._db.execute(
            """INSERT INTO project_manifest (project_path, manifest_json, updated_at)
               VALUES (?, ?, ?)
               ON CONFLICT(project_path) DO UPDATE SET manifest_json=excluded.manifest_json, updated_at=excluded.updated_at""",
            (project_path, json.dumps(manifest), datetime.utcnow().isoformat()),
        )
        await self._db.commit()

    async def get_manifest(self, project_path: str) -> dict | None:
        cursor = await self._db.execute(
            "SELECT manifest_json FROM project_manifest WHERE project_path = ?",
            (project_path,),
        )
        row = await cursor.fetchone()
        return json.loads(row[0]) if row else None
