from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig

from jarvis.db.repositories import NoteRepo
from jarvis.tools import get_user_context


@tool
async def save_note(
    title: str,
    content: str,
    category: str = "",
    is_pinned: bool = False,
    *,
    config: RunnableConfig,
) -> str:
    """Save a structured note with a title and content. Category: work, personal, tech, etc."""
    ctx = get_user_context(config)
    await NoteRepo.save(ctx.user_id, title, content, category or None, is_pinned)
    pin = " (pinned)" if is_pinned else ""
    cat = f" [{category}]" if category else ""
    return f"Note saved{pin}{cat}: {title}"


@tool
async def search_notes(query: str, *, config: RunnableConfig) -> str:
    """Search notes using smart search (keyword + semantic meaning).
    Finds notes even if the exact words don't match."""
    ctx = get_user_context(config)
    results = await NoteRepo.smart_search(ctx.user_id, query)
    if not results:
        return "No notes found matching that query."
    lines = []
    for row in results:
        pin = " (pinned)" if row.get("is_pinned") else ""
        cat = f" [{row['category']}]" if row.get("category") else ""
        score = f" | relevance: {row['_relevance']:.0%}" if "_relevance" in row else ""
        lines.append(f"#{row['id']} - **{row['title']}**{pin}{cat}{score}\n{row['content'][:200]}")
    return "\n\n".join(lines)


@tool
async def list_notes(*, config: RunnableConfig) -> str:
    """List all saved notes (titles only)."""
    ctx = get_user_context(config)
    rows = await NoteRepo.list_all(ctx.user_id)
    if not rows:
        return "No notes saved yet."
    lines = []
    for row in rows:
        pin = " (pinned)" if row.get("is_pinned") else ""
        cat = f" [{row['category']}]" if row.get("category") else ""
        lines.append(f"#{row['id']}: {row['title']}{pin}{cat} ({row['created_at']})")
    return "\n".join(lines)


@tool
async def delete_note(note_id: int, *, config: RunnableConfig) -> str:
    """Delete a note by its ID."""
    ctx = get_user_context(config)
    success = await NoteRepo.delete(ctx.user_id, note_id)
    if not success:
        return f"Note #{note_id} not found."
    return f"Note #{note_id} deleted."
