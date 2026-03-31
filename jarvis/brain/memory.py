# Legacy module — kept for backward compatibility.
# Use jarvis.db.repositories.ConversationRepo instead.

from jarvis.db.repositories import ConversationRepo


async def save_message(chat_id: str, role: str, content: str):
    """Deprecated: use ConversationRepo.save_message()."""
    await ConversationRepo.save_message(user_id="legacy", chat_id=chat_id, role=role, content=content)


async def get_history(chat_id: str) -> list[dict]:
    """Deprecated: use ConversationRepo.get_history()."""
    from jarvis.config import settings
    return await ConversationRepo.get_history(chat_id, settings.MEMORY_WINDOW)


async def clear_history(chat_id: str):
    """Deprecated: use ConversationRepo.clear_history()."""
    await ConversationRepo.clear_history(chat_id)
