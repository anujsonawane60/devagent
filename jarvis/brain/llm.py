# Legacy module — kept for backward compatibility.
# Use jarvis.core.llm_factory instead.

from jarvis.core.llm_factory import create_llm


def get_llm():
    """Deprecated: use create_llm() from jarvis.core.llm_factory."""
    return create_llm()
