from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig

from jarvis.db.repositories import NoteRepo
from jarvis.tools import get_user_context


@tool
async def save_note(title: str, content: str, *, config: RunnableConfig) -> str:
    """Save a personal note. Use this when the user wants to remember something, store information, or save a snippet."""
    ctx = get_user_context(config)
    await NoteRepo.save(ctx.user_id, title, content)
    return f"Note saved: {title}"


@tool
async def search_notes(query: str, *, config: RunnableConfig) -> str:
    """Search through saved notes by keyword."""
    ctx = get_user_context(config)
    rows = await NoteRepo.search(ctx.user_id, query)
    if not rows:
        return "No notes found matching that query."
    lines = []
    for row in rows:
        lines.append(f"#{row['id']} - **{row['title']}**\n{row['content']}")
    return "\n\n".join(lines)


@tool
async def list_notes(*, config: RunnableConfig) -> str:
    """List all saved notes (titles only)."""
    ctx = get_user_context(config)
    rows = await NoteRepo.list_all(ctx.user_id)
    if not rows:
        return "No notes saved yet."
    lines = [f"#{row['id']}: {row['title']} ({row['created_at']})" for row in rows]
    return "\n".join(lines)
