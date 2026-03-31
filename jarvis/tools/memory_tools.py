from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig

from jarvis.db.repositories import MemoryRepo
from jarvis.tools import get_user_context


@tool
async def learn_fact(
    fact: str,
    category: str = "fact",
    *,
    config: RunnableConfig,
) -> str:
    """Learn and remember a fact about the user. If the same fact is learned again, confidence increases.
    Category can be: preference, fact, opinion, habit, relationship.
    Examples: 'User prefers Python over Java', 'User's mom is Sunita', 'User wakes up at 6 AM'."""
    ctx = get_user_context(config)
    await MemoryRepo.learn(ctx.user_id, fact, category)
    return f"Remembered: {fact}"


@tool
async def recall(query: str, category: str = "", *, config: RunnableConfig) -> str:
    """Recall learned facts about the user using smart search (keyword + semantic).
    Optionally filter by category: preference, fact, opinion, habit, relationship."""
    ctx = get_user_context(config)
    results = await MemoryRepo.smart_recall(ctx.user_id, query)
    if not results:
        return "I don't recall anything matching that."
    lines = []
    for m in results:
        conf = f"{m['confidence']:.0%}"
        score = f" | relevance: {m['_relevance']:.0%}" if "_relevance" in m else ""
        lines.append(f"- [{m['category']}] {m['fact']} (confidence: {conf}){score}")
    return "\n".join(lines)


@tool
async def forget(memory_id: int, *, config: RunnableConfig) -> str:
    """Forget a specific learned fact by its ID. The user asked to remove this memory."""
    ctx = get_user_context(config)
    success = await MemoryRepo.forget(ctx.user_id, memory_id)
    if not success:
        return f"Memory #{memory_id} not found."
    return f"Memory #{memory_id} forgotten."
