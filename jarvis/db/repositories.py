from jarvis.db.database import get_db


class ConversationRepo:
    @staticmethod
    async def save_message(user_id: str, chat_id: str, role: str, content: str):
        db = await get_db()
        await db.execute(
            "INSERT INTO conversations (user_id, chat_id, role, content) VALUES (?, ?, ?, ?)",
            (user_id, chat_id, role, content),
        )
        await db.commit()

    @staticmethod
    async def get_history(chat_id: str, limit: int = 20) -> list[dict]:
        db = await get_db()
        cursor = await db.execute(
            "SELECT role, content FROM conversations WHERE chat_id = ? ORDER BY id DESC LIMIT ?",
            (chat_id, limit),
        )
        rows = await cursor.fetchall()
        return [{"role": row["role"], "content": row["content"]} for row in reversed(rows)]

    @staticmethod
    async def clear_history(chat_id: str):
        db = await get_db()
        await db.execute("DELETE FROM conversations WHERE chat_id = ?", (chat_id,))
        await db.commit()


class TaskRepo:
    @staticmethod
    async def create(user_id: str, title: str, due_date: str | None = None) -> int:
        db = await get_db()
        cursor = await db.execute(
            "INSERT INTO tasks (user_id, title, due_date) VALUES (?, ?, ?)",
            (user_id, title, due_date),
        )
        await db.commit()
        return cursor.lastrowid

    @staticmethod
    async def list_tasks(user_id: str, status: str = "pending") -> list[dict]:
        db = await get_db()
        if status == "all":
            cursor = await db.execute(
                "SELECT id, title, due_date, status FROM tasks WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,),
            )
        else:
            cursor = await db.execute(
                "SELECT id, title, due_date, status FROM tasks WHERE user_id = ? AND status = ? ORDER BY created_at DESC",
                (user_id, status),
            )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    async def complete(user_id: str, task_id: int) -> bool:
        db = await get_db()
        cursor = await db.execute(
            "UPDATE tasks SET status = 'completed', completed_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?",
            (task_id, user_id),
        )
        await db.commit()
        return cursor.rowcount > 0


class NoteRepo:
    @staticmethod
    async def save(user_id: str, title: str, content: str) -> int:
        db = await get_db()
        cursor = await db.execute(
            "INSERT INTO notes (user_id, title, content) VALUES (?, ?, ?)",
            (user_id, title, content),
        )
        await db.commit()
        return cursor.lastrowid

    @staticmethod
    async def search(user_id: str, query: str, limit: int = 10) -> list[dict]:
        db = await get_db()
        cursor = await db.execute(
            "SELECT id, title, content FROM notes WHERE user_id = ? AND (title LIKE ? OR content LIKE ?) ORDER BY updated_at DESC LIMIT ?",
            (user_id, f"%{query}%", f"%{query}%", limit),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    async def list_all(user_id: str, limit: int = 20) -> list[dict]:
        db = await get_db()
        cursor = await db.execute(
            "SELECT id, title, created_at FROM notes WHERE user_id = ? ORDER BY updated_at DESC LIMIT ?",
            (user_id, limit),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


class UserRepo:
    @staticmethod
    async def upsert(user_id: str, platform: str, username: str | None = None, display_name: str | None = None):
        db = await get_db()
        await db.execute(
            """INSERT INTO users (id, platform, username, display_name)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET
                   last_seen = CURRENT_TIMESTAMP,
                   username = COALESCE(excluded.username, users.username),
                   display_name = COALESCE(excluded.display_name, users.display_name)
            """,
            (user_id, platform, username, display_name),
        )
        await db.commit()
