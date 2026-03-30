from langchain_core.tools import tool
from jarvis.db.database import get_db


@tool
async def save_note(title: str, content: str) -> str:
    """Save a personal note. Use this when the user wants to remember something, store information, or save a snippet."""
    db = await get_db()
    try:
        await db.execute(
            "INSERT INTO notes (chat_id, title, content) VALUES ('global', ?, ?)",
            (title, content),
        )
        await db.commit()
        return f"Note saved: {title}"
    finally:
        await db.close()


@tool
async def search_notes(query: str) -> str:
    """Search through saved notes by keyword."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT id, title, content FROM notes WHERE chat_id = 'global' AND (title LIKE ? OR content LIKE ?) ORDER BY updated_at DESC LIMIT 10",
            (f"%{query}%", f"%{query}%"),
        )
        rows = await cursor.fetchall()
        if not rows:
            return "No notes found matching that query."
        lines = []
        for row in rows:
            lines.append(f"#{row[0]} - **{row[1]}**\n{row[2]}")
        return "\n\n".join(lines)
    finally:
        await db.close()


@tool
async def list_notes() -> str:
    """List all saved notes (titles only)."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT id, title, created_at FROM notes WHERE chat_id = 'global' ORDER BY updated_at DESC LIMIT 20"
        )
        rows = await cursor.fetchall()
        if not rows:
            return "No notes saved yet."
        lines = [f"#{row[0]}: {row[1]} ({row[2]})" for row in rows]
        return "\n".join(lines)
    finally:
        await db.close()
