"""SQLite FTS5 search engine for code entities."""

from dataclasses import dataclass
from typing import Optional, List

from code_engine.parser import CodeParser, CodeEntity
from storage.db import Database


@dataclass
class SearchResult:
    """A single search result."""
    file_path: str
    entity_name: str
    entity_type: str
    line: int
    snippet: str
    score: float


class CodeSearchEngine:
    """Indexes projects and searches code entities via FTS5."""

    def __init__(self, db: Database):
        self.db = db

    async def index_project(self, project_path: str, parser: CodeParser) -> int:
        """Parse all files in a project and store entities in the database.

        Returns the number of entities indexed.
        """
        # Clear existing index for this project
        await self.db.clear_project_index(project_path)

        results = parser.parse_project(project_path)
        total = 0

        for file_result in results:
            entities = []
            for entity in file_result.entities:
                entities.append({
                    "file_path": entity.file_path,
                    "entity_type": entity.type,
                    "name": entity.name,
                    "line_start": entity.line_start,
                    "line_end": entity.line_end,
                    "signature": entity.signature or "",
                    "docstring": entity.docstring or "",
                })
            if entities:
                await self.db.save_entities(project_path, entities)
                total += len(entities)

            # Store dependencies from imports
            deps = []
            for imp in file_result.imports:
                deps.append({
                    "source_file": file_result.file_path,
                    "target_file": imp,  # raw import text; resolution is future work
                    "import_name": imp,
                })
            if deps:
                await self.db.save_dependencies(project_path, deps)

        return total

    async def search(self, query: str, project_path: Optional[str] = None, limit: int = 10) -> List[SearchResult]:
        """Search code entities using FTS5."""
        rows = await self.db.search_code(query, project_path=project_path, limit=limit)
        results = []
        for row in rows:
            snippet = row.get("signature") or row.get("name", "")
            if row.get("docstring"):
                snippet += f" — {row['docstring']}"
            results.append(SearchResult(
                file_path=row["file_path"],
                entity_name=row["name"],
                entity_type=row["entity_type"],
                line=row.get("line_start", 0),
                snippet=snippet,
                score=row.get("score", 0.0),
            ))
        return results

    async def find_definition(self, name: str, project_path: Optional[str] = None) -> Optional[dict]:
        """Find an exact entity by name."""
        results = await self.db.search_code(name, project_path=project_path, limit=5)
        for r in results:
            if r["name"] == name:
                return r
        return None

    async def get_file_context(self, file_path: str) -> dict:
        """Get entities and dependencies for a specific file."""
        deps = await self.db.get_dependencies(file_path)
        return {
            "file_path": file_path,
            "dependencies": deps,
        }
