"""
Embedding provider — converts text to vectors for semantic search.

Supports OpenAI (paid, best quality) and Ollama (free, local).
Configured via EMBEDDING_PROVIDER and EMBEDDING_MODEL in .env.
"""

import logging
from langchain_core.embeddings import Embeddings

from jarvis.config import settings

logger = logging.getLogger(__name__)

_embeddings: Embeddings | None = None


def get_embeddings() -> Embeddings:
    """Get or create the singleton embedding model."""
    global _embeddings
    if _embeddings is not None:
        return _embeddings

    provider = settings.EMBEDDING_PROVIDER
    model = settings.EMBEDDING_MODEL

    if provider == "openai":
        from langchain_openai import OpenAIEmbeddings

        _embeddings = OpenAIEmbeddings(
            model=model,
            api_key=settings.OPENAI_API_KEY,
        )
        logger.info(f"Embedding provider: OpenAI ({model})")

    elif provider == "ollama":
        from langchain_ollama import OllamaEmbeddings

        _embeddings = OllamaEmbeddings(model=model)
        logger.info(f"Embedding provider: Ollama ({model})")

    else:
        raise ValueError(f"Unknown embedding provider: {provider}")

    return _embeddings
