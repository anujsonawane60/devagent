"""Context retrieval for LLM tasks."""

from dataclasses import dataclass, field
from typing import List, Optional

from code_engine.search import CodeSearchEngine


@dataclass
class ContextFile:
    """A file included in the context."""
    path: str
    entities: List[dict] = field(default_factory=list)
    relevance_score: float = 0.0
    content_preview: str = ""


@dataclass
class ContextResult:
    """Result of context retrieval."""
    files: List[ContextFile] = field(default_factory=list)
    total_entities: int = 0
    query: str = ""


class ContextBuilder:
    """Builds LLM-ready context from search results and dependency graph."""

    def __init__(self, search_engine: CodeSearchEngine):
        self.search_engine = search_engine

    async def get_context(
        self, query: str, project_path: str, max_files: int = 15, token_budget: int = 4000
    ) -> ContextResult:
        """Retrieve relevant context for a query.

        1. Search FTS5 for matching entities
        2. Expand with dependency graph
        3. Rank by relevance
        4. Trim to fit token budget
        """
        result = ContextResult(query=query)

        if not query.strip():
            return result

        # Step 1: Search for matching entities
        search_results = await self.search_engine.search(query, project_path=project_path, limit=20)

        # Step 2: Group by file and build context files
        file_map: dict[str, ContextFile] = {}
        for sr in search_results:
            if sr.file_path not in file_map:
                file_map[sr.file_path] = ContextFile(
                    path=sr.file_path,
                    relevance_score=abs(sr.score) if sr.score else 0.0,
                )
            cf = file_map[sr.file_path]
            cf.entities.append({
                "name": sr.entity_name,
                "type": sr.entity_type,
                "line": sr.line,
                "snippet": sr.snippet,
            })
            # Increase relevance for more matches in the same file
            cf.relevance_score += 1.0

        # Step 3: Expand with dependencies
        dep_files = set()
        for fpath in list(file_map.keys()):
            file_ctx = await self.search_engine.get_file_context(fpath)
            for dep in file_ctx.get("dependencies", []):
                if dep not in file_map:
                    dep_files.add(dep)

        for dep_path in dep_files:
            if dep_path not in file_map:
                file_map[dep_path] = ContextFile(
                    path=dep_path,
                    relevance_score=0.5,  # Lower score for dependency-only files
                )

        # Step 4: Sort by relevance and trim
        sorted_files = sorted(file_map.values(), key=lambda f: f.relevance_score, reverse=True)
        sorted_files = sorted_files[:max_files]

        # Trim to token budget (rough estimate: 4 chars per token)
        total_chars = 0
        budget_chars = token_budget * 4
        trimmed = []
        for cf in sorted_files:
            preview = self._build_preview(cf)
            cf.content_preview = preview
            total_chars += len(preview)
            if total_chars > budget_chars and trimmed:
                break
            trimmed.append(cf)

        result.files = trimmed
        result.total_entities = sum(len(f.entities) for f in trimmed)
        return result

    def format_context(self, context_result: ContextResult) -> str:
        """Format context for inclusion in an LLM prompt."""
        if not context_result.files:
            return f"No relevant code found for: {context_result.query}"

        parts = [f"## Code Context for: {context_result.query}\n"]
        for cf in context_result.files:
            parts.append(f"### {cf.path}")
            if cf.content_preview:
                parts.append(cf.content_preview)
            parts.append("")

        parts.append(f"_Total: {context_result.total_entities} entities from {len(context_result.files)} files_")
        return "\n".join(parts)

    def _build_preview(self, cf: ContextFile) -> str:
        """Build a text preview of a context file's entities."""
        lines = []
        for entity in cf.entities:
            lines.append(f"  L{entity['line']}: [{entity['type']}] {entity['snippet']}")
        return "\n".join(lines) if lines else f"  (dependency: {cf.path})"
