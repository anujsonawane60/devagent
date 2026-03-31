from langchain_core.runnables import RunnableConfig

from jarvis.core.context import UserContext


def get_user_context(config: RunnableConfig) -> UserContext:
    """Extract UserContext from LangGraph's RunnableConfig."""
    ctx_data = config.get("configurable", {}).get("user_context", {})
    if not ctx_data:
        # Fallback for tools called without context (e.g., during testing)
        return UserContext(user_id="unknown", chat_id="unknown", platform="unknown")
    return UserContext.from_dict(ctx_data)
