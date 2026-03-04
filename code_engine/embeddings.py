"""Code embeddings for semantic search using ChromaDB."""

import hashlib
import logging
from dataclasses import dataclass, field
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class SemanticResult:
    """A single semantic search result."""
    entity_name: str
    entity_type: str
    file_path: str
    line: int
    snippet: str
    score: float
    metadata: dict = field(default_factory=dict)


class SemanticSearch:
    """Semantic code search using ChromaDB for embeddings."""

    def __init__(self, persist_path: str = "devagent_chroma", collection_name: str = "code_entities"):
        self.persist_path = persist_path
        self.collection_name = collection_name
        self._client = None
        self._collection = None

    def _get_collection(self):
        """Lazily initialize ChromaDB client and collection."""
        if self._collection is None:
            import chromadb
            self._client = chromadb.PersistentClient(path=self.persist_path)
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        return self._collection

    def _entity_id(self, file_path: str, name: str, line: int) -> str:
        """Generate a stable ID for an entity."""
        raw = f"{file_path}:{name}:{line}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def index_entities(self, entities: List[dict], project_path: str) -> int:
        """Index code entities into ChromaDB.

        Each entity dict should have: name, type, file_path, line_start, signature, docstring
        """
        collection = self._get_collection()

        ids = []
        documents = []
        metadatas = []

        for entity in entities:
            name = entity.get("name", "")
            etype = entity.get("type", "")
            fpath = entity.get("file_path", "")
            line = entity.get("line_start", 0)
            sig = entity.get("signature", "")
            doc = entity.get("docstring", "")

            # Build searchable document from entity info
            doc_text = f"{etype} {name}"
            if sig:
                doc_text += f"\n{sig}"
            if doc:
                doc_text += f"\n{doc}"

            entity_id = self._entity_id(fpath, name, line)
            ids.append(entity_id)
            documents.append(doc_text)
            metadatas.append({
                "entity_name": name,
                "entity_type": etype,
                "file_path": fpath,
                "line": line,
                "project_path": project_path,
                "signature": sig,
            })

        if not ids:
            return 0

        # Upsert in batches of 100
        batch_size = 100
        for i in range(0, len(ids), batch_size):
            batch_end = min(i + batch_size, len(ids))
            collection.upsert(
                ids=ids[i:batch_end],
                documents=documents[i:batch_end],
                metadatas=metadatas[i:batch_end],
            )

        logger.info(f"Indexed {len(ids)} entities into ChromaDB for {project_path}")
        return len(ids)

    def search(
        self, query: str, project_path: Optional[str] = None, limit: int = 10
    ) -> List[SemanticResult]:
        """Semantic search for code entities similar to the query."""
        collection = self._get_collection()

        where_filter = None
        if project_path:
            where_filter = {"project_path": project_path}

        try:
            results = collection.query(
                query_texts=[query],
                n_results=limit,
                where=where_filter,
            )
        except Exception as e:
            logger.warning(f"ChromaDB query failed: {e}")
            return []

        semantic_results = []
        if results and results["ids"] and results["ids"][0]:
            for i, entity_id in enumerate(results["ids"][0]):
                meta = results["metadatas"][0][i] if results["metadatas"] else {}
                distance = results["distances"][0][i] if results["distances"] else 0.0
                score = 1.0 - distance  # Convert distance to similarity

                semantic_results.append(SemanticResult(
                    entity_name=meta.get("entity_name", ""),
                    entity_type=meta.get("entity_type", ""),
                    file_path=meta.get("file_path", ""),
                    line=meta.get("line", 0),
                    snippet=meta.get("signature", ""),
                    score=score,
                    metadata=meta,
                ))

        return semantic_results

    def clear_project(self, project_path: str) -> None:
        """Remove all entities for a project from the collection."""
        collection = self._get_collection()
        try:
            existing = collection.get(where={"project_path": project_path})
            if existing["ids"]:
                collection.delete(ids=existing["ids"])
                logger.info(f"Cleared {len(existing['ids'])} entities for {project_path}")
        except Exception as e:
            logger.warning(f"Failed to clear project from ChromaDB: {e}")

    def count(self) -> int:
        """Return total number of indexed entities."""
        collection = self._get_collection()
        return collection.count()
