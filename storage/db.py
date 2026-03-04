"""SQLite storage via aiosqlite."""

import json
from datetime import datetime
from typing import Optional

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
        await self._db.execute("""
            CREATE TABLE IF NOT EXISTS code_entities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_path TEXT NOT NULL,
                file_path TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                name TEXT NOT NULL,
                line_start INTEGER,
                line_end INTEGER,
                signature TEXT,
                docstring TEXT,
                updated_at TEXT NOT NULL
            )
        """)
        await self._db.execute("""
            CREATE TABLE IF NOT EXISTS file_dependencies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_path TEXT NOT NULL,
                source_file TEXT NOT NULL,
                target_file TEXT NOT NULL,
                import_name TEXT
            )
        """)
        # FTS5 virtual table for full-text search on code entities
        await self._db.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS code_search USING fts5(
                name, signature, docstring, file_path,
                content='code_entities', content_rowid='id'
            )
        """)
        await self._db.commit()

    # --- Command log ---

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

    # --- Project manifest ---

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

    # --- Code entities ---

    async def save_entities(self, project_path: str, entities: list[dict]) -> None:
        """Bulk insert parsed code entities and update FTS index."""
        now = datetime.utcnow().isoformat()
        for entity in entities:
            cursor = await self._db.execute(
                """INSERT INTO code_entities
                   (project_path, file_path, entity_type, name, line_start, line_end, signature, docstring, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    project_path,
                    entity["file_path"],
                    entity["entity_type"],
                    entity["name"],
                    entity.get("line_start"),
                    entity.get("line_end"),
                    entity.get("signature", ""),
                    entity.get("docstring", ""),
                    now,
                ),
            )
            # Sync FTS index
            row_id = cursor.lastrowid
            await self._db.execute(
                "INSERT INTO code_search(rowid, name, signature, docstring, file_path) VALUES (?, ?, ?, ?, ?)",
                (row_id, entity["name"], entity.get("signature", ""), entity.get("docstring", ""), entity["file_path"]),
            )
        await self._db.commit()

    async def search_code(self, query: str, project_path: Optional[str] = None, limit: int = 10) -> list[dict]:
        """Full-text search on code entities via FTS5."""
        # Build FTS5 query - escape special chars and add prefix matching
        fts_query = self._build_fts_query(query)
        if not fts_query:
            return []

        if project_path:
            cursor = await self._db.execute(
                """SELECT ce.id, ce.file_path, ce.entity_type, ce.name, ce.line_start,
                          ce.line_end, ce.signature, ce.docstring,
                          rank
                   FROM code_search cs
                   JOIN code_entities ce ON cs.rowid = ce.id
                   WHERE code_search MATCH ? AND ce.project_path = ?
                   ORDER BY rank
                   LIMIT ?""",
                (fts_query, project_path, limit),
            )
        else:
            cursor = await self._db.execute(
                """SELECT ce.id, ce.file_path, ce.entity_type, ce.name, ce.line_start,
                          ce.line_end, ce.signature, ce.docstring,
                          rank
                   FROM code_search cs
                   JOIN code_entities ce ON cs.rowid = ce.id
                   WHERE code_search MATCH ?
                   ORDER BY rank
                   LIMIT ?""",
                (fts_query, limit),
            )
        rows = await cursor.fetchall()
        return [
            {
                "id": r[0],
                "file_path": r[1],
                "entity_type": r[2],
                "name": r[3],
                "line_start": r[4],
                "line_end": r[5],
                "signature": r[6],
                "docstring": r[7],
                "score": r[8],
            }
            for r in rows
        ]

    def _build_fts_query(self, query: str) -> str:
        """Build an FTS5 query from user input."""
        # Split into tokens and add prefix matching
        tokens = query.strip().split()
        if not tokens:
            return ""
        # Escape double quotes and wrap each token
        parts = []
        for t in tokens:
            t = t.replace('"', '')
            if t:
                parts.append(f'"{t}"')
        return " OR ".join(parts) if parts else ""

    # --- File dependencies ---

    async def save_dependencies(self, project_path: str, deps: list[dict]) -> None:
        """Store import graph edges."""
        for dep in deps:
            await self._db.execute(
                "INSERT INTO file_dependencies (project_path, source_file, target_file, import_name) VALUES (?, ?, ?, ?)",
                (project_path, dep["source_file"], dep["target_file"], dep.get("import_name", "")),
            )
        await self._db.commit()

    async def get_dependencies(self, file_path: str) -> list[str]:
        """Get files related to the given file (imports and imported by)."""
        cursor = await self._db.execute(
            """SELECT DISTINCT target_file FROM file_dependencies WHERE source_file = ?
               UNION
               SELECT DISTINCT source_file FROM file_dependencies WHERE target_file = ?""",
            (file_path, file_path),
        )
        rows = await cursor.fetchall()
        return [r[0] for r in rows]

    async def clear_project_index(self, project_path: str) -> None:
        """Wipe all indexed data for a project before re-indexing."""
        # Get entity data for FTS cleanup (must provide original values for content= tables)
        cursor = await self._db.execute(
            "SELECT id, name, signature, docstring, file_path FROM code_entities WHERE project_path = ?",
            (project_path,),
        )
        rows = await cursor.fetchall()
        for row in rows:
            await self._db.execute(
                "INSERT INTO code_search(code_search, rowid, name, signature, docstring, file_path) VALUES('delete', ?, ?, ?, ?, ?)",
                (row[0], row[1], row[2] or "", row[3] or "", row[4]),
            )

        await self._db.execute("DELETE FROM code_entities WHERE project_path = ?", (project_path,))
        await self._db.execute("DELETE FROM file_dependencies WHERE project_path = ?", (project_path,))
        await self._db.commit()
