from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig

from jarvis.db.repositories import ThoughtRepo
from jarvis.tools import get_user_context


@tool
async def save_thought(
    content: str,
    thought_type: str = "random",
    mood: str = "",
    is_private: bool = False,
    *,
    config: RunnableConfig,
) -> str:
    """Save a quick thought, idea, opinion, or random note. Zero friction — just dump it.
    thought_type can be: idea, opinion, fact, random, bookmark, quote, snippet, question.
    Set is_private=true for sensitive thoughts (encrypted in DB)."""
    ctx = get_user_context(config)
    await ThoughtRepo.save(
        user_id=ctx.user_id,
        content=content,
        thought_type=thought_type,
        mood=mood or None,
        source=ctx.platform,
        is_private=is_private,
    )
    label = thought_type if thought_type != "random" else "thought"
    private_tag = " (private)" if is_private else ""
    return f"Saved {label}{private_tag}: {content[:80]}{'...' if len(content) > 80 else ''}"


@tool
async def search_thoughts(query: str, *, config: RunnableConfig) -> str:
    """Search through saved thoughts using smart search (keyword + semantic meaning).
    Finds thoughts even if the exact words don't match."""
    ctx = get_user_context(config)
    results = await ThoughtRepo.smart_search(ctx.user_id, query)
    if not results:
        return "No thoughts found matching that query."
    lines = []
    for t in results:
        prefix = f"[{t['thought_type']}]" if t.get("thought_type") != "random" else ""
        pin = " (pinned)" if t.get("is_pinned") else ""
        score = f" | relevance: {t['_relevance']:.0%}" if "_relevance" in t else ""
        lines.append(f"#{t['id']} {prefix}{pin} {t['content'][:120]}{score}")
    return "\n".join(lines)


@tool
async def list_thoughts(
    thought_type: str = "",
    limit: int = 15,
    *,
    config: RunnableConfig,
) -> str:
    """List saved thoughts, optionally filtered by type (idea, opinion, fact, random, bookmark, quote, snippet, question)."""
    ctx = get_user_context(config)
    results = await ThoughtRepo.list_by_type(
        ctx.user_id,
        thought_type=thought_type or None,
        limit=limit,
    )
    if not results:
        return f"No {thought_type + ' ' if thought_type else ''}thoughts found."
    lines = []
    for t in results:
        prefix = f"[{t['thought_type']}]" if t.get("thought_type") != "random" else ""
        pin = " (pinned)" if t.get("is_pinned") else ""
        private = " (private)" if t.get("is_private") else ""
        lines.append(f"#{t['id']} {prefix}{pin}{private} {t['content'][:120]}")
    return "\n".join(lines)


@tool
async def pin_thought(thought_id: int, *, config: RunnableConfig) -> str:
    """Pin an important thought so it stands out."""
    ctx = get_user_context(config)
    success = await ThoughtRepo.pin(ctx.user_id, thought_id, pinned=True)
    if not success:
        return f"Thought #{thought_id} not found."
    return f"Thought #{thought_id} pinned."


@tool
async def delete_thought(thought_id: int, *, config: RunnableConfig) -> str:
    """Delete a thought by its ID."""
    ctx = get_user_context(config)
    success = await ThoughtRepo.delete(ctx.user_id, thought_id)
    if not success:
        return f"Thought #{thought_id} not found."
    return f"Thought #{thought_id} deleted."
