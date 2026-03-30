from jarvis.db.database import get_db
from jarvis.config import settings


async def save_message(chat_id: str, role: str, content: str):
    db = await get_db()
    try:
        await db.execute(
            "INSERT INTO conversations (chat_id, role, content) VALUES (?, ?, ?)",
            (chat_id, role, content),
        )
        await db.commit()
    finally:
        await db.close()


async def get_history(chat_id: str) -> list[dict]:
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT role, content FROM conversations WHERE chat_id = ? ORDER BY id DESC LIMIT ?",
            (chat_id, settings.MEMORY_WINDOW),
        )
        rows = await cursor.fetchall()
        return [{"role": row[0], "content": row[1]} for row in reversed(rows)]
    finally:
        await db.close()


async def clear_history(chat_id: str):
    db = await get_db()
    try:
        await db.execute("DELETE FROM conversations WHERE chat_id = ?", (chat_id,))
        await db.commit()
    finally:
        await db.close()
