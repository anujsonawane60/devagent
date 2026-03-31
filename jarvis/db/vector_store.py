"""
Semantic search layer powered by ChromaDB.

Each user gets their own collection (data isolation).
Stores embeddings alongside SQLite — SQLite is the source of truth,
ChromaDB is a search index that can be rebuilt from SQL data.

Usage:
    # Store (called after saving to SQL)
    await VectorStore.store(user_id, "thought", 42, "I should learn Rust")

    # Search (semantic — finds by meaning, not keywords)
    results = await VectorStore.search(user_id, "programming languages to learn")
    # → [{"text": "I should learn Rust", "score": 0.89, ...}]

    # Delete (called when source entity is deleted)
    await VectorStore.delete(user_id, "thought", 42)
"""

import logging
import os

import chromadb

from jarvis.config import settings
from jarvis.db.embeddings import get_embeddings

logger = logging.getLogger(__name__)

_client: chromadb.ClientAPI | None = None


def _get_client() -> chromadb.ClientAPI:
    """Get or create the singleton ChromaDB client."""
    global _client
    if _client is None:
        os.makedirs(settings.VECTOR_DB_PATH, exist_ok=True)
        _client = chromadb.PersistentClient(path=settings.VECTOR_DB_PATH)
        logger.info(f"ChromaDB initialized at {settings.VECTOR_DB_PATH}")
    return _client


def _collection_name(user_id: str) -> str:
    """Each user gets their own collection for data isolation."""
    # ChromaDB collection names: 3-63 chars, alphanumeric + underscores
    safe_id = user_id.replace("-", "_")
    return f"user_{safe_id}"


class VectorStore:
    """Async-compatible semantic search layer on ChromaDB."""

    @staticmethod
    async def store(
        user_id: str,
        entity_type: str,
        entity_id: int,
        text: str,
        metadata: dict | None = None,
    ):
        """
        Store text with its embedding vector.

        Call this after saving to SQL:
            thought_id = await ThoughtRepo.save(...)
            await VectorStore.store(user_id, "thought", thought_id, content)

        Args:
            entity_type: "thought", "note", "memory", "contact"
            entity_id: the SQL row ID
            text: the content to embed
            metadata: extra fields for filtering (e.g., thought_type)
        """
        if not settings.VECTOR_DB_ENABLED or not text.strip():
            return

        try:
            client = _get_client()
            collection = client.get_or_create_collection(
                name=_collection_name(user_id),
                metadata={"hnsw:space": "cosine"},
            )

            embeddings_model = get_embeddings()
            vector = embeddings_model.embed_query(text)

            doc_id = f"{entity_type}_{entity_id}"
            doc_metadata = {
                "entity_type": entity_type,
                "entity_id": entity_id,
                "user_id": user_id,
                **(metadata or {}),
            }

            # Upsert — handles both insert and update
            collection.upsert(
                ids=[doc_id],
                embeddings=[vector],
                documents=[text],
                metadatas=[doc_metadata],
            )
            logger.debug(f"Vector stored: {doc_id} for user {user_id}")

        except Exception as e:
            # Vector store failure should NOT break the main flow
            logger.error(f"Vector store failed for {entity_type}_{entity_id}: {e}")

    @staticmethod
    async def search(
        user_id: str,
        query: str,
        entity_type: str | None = None,
        limit: int = 10,
        min_score: float = 0.3,
    ) -> list[dict]:
        """
        Find semantically similar content.

        Args:
            query: natural language search query
            entity_type: filter to specific type ("thought", "note", etc.)
            limit: max results
            min_score: minimum similarity score (0-1, higher = more similar)

        Returns:
            List of dicts with: text, score, entity_type, entity_id, metadata
        """
        if not settings.VECTOR_DB_ENABLED:
            return []

        try:
            client = _get_client()
            col_name = _collection_name(user_id)

            # Check if collection exists
            existing = [c.name for c in client.list_collections()]
            if col_name not in existing:
                return []

            collection = client.get_collection(name=col_name)

            if collection.count() == 0:
                return []

            embeddings_model = get_embeddings()
            query_vector = embeddings_model.embed_query(query)

            where = {"entity_type": entity_type} if entity_type else None

            results = collection.query(
                query_embeddings=[query_vector],
                n_results=min(limit, collection.count()),
                where=where,
                include=["documents", "metadatas", "distances"],
            )

            matches = []
            for i, doc in enumerate(results["documents"][0]):
                # ChromaDB returns cosine distance; convert to similarity
                distance = results["distances"][0][i]
                score = 1 - distance

                if score < min_score:
                    continue

                matches.append({
                    "text": doc,
                    "score": round(score, 4),
                    "entity_type": results["metadatas"][0][i].get("entity_type", ""),
                    "entity_id": results["metadatas"][0][i].get("entity_id", 0),
                    "metadata": results["metadatas"][0][i],
                })

            return matches

        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []

    @staticmethod
    async def delete(user_id: str, entity_type: str, entity_id: int):
        """Remove an embedding when the source entity is deleted from SQL."""
        if not settings.VECTOR_DB_ENABLED:
            return

        try:
            client = _get_client()
            col_name = _collection_name(user_id)

            existing = [c.name for c in client.list_collections()]
            if col_name not in existing:
                return

            collection = client.get_collection(name=col_name)
            doc_id = f"{entity_type}_{entity_id}"
            collection.delete(ids=[doc_id])
            logger.debug(f"Vector deleted: {doc_id}")

        except Exception as e:
            logger.error(f"Vector delete failed: {e}")

    @staticmethod
    async def delete_user(user_id: str):
        """Delete all vectors for a user (GDPR / account deletion)."""
        if not settings.VECTOR_DB_ENABLED:
            return

        try:
            client = _get_client()
            col_name = _collection_name(user_id)
            existing = [c.name for c in client.list_collections()]
            if col_name in existing:
                client.delete_collection(name=col_name)
                logger.info(f"Deleted all vectors for user {user_id}")
        except Exception as e:
            logger.error(f"Vector user deletion failed: {e}")

    @staticmethod
    def close():
        """Release ChromaDB client."""
        global _client
        _client = None
