"""Business logic for bot commands."""

from code_engine.analyzer import ProjectAnalyzer
from code_engine.parser import CodeParser
from code_engine.search import CodeSearchEngine
from storage.db import Database


class CommandHandler:
    def __init__(
        self,
        analyzer: ProjectAnalyzer | None = None,
        db: Database | None = None,
    ):
        self.analyzer = analyzer or ProjectAnalyzer()
        self.db = db
        self._search_engine: CodeSearchEngine | None = None
        self._parser: CodeParser | None = None

    @property
    def search_engine(self) -> CodeSearchEngine | None:
        if self._search_engine is None and self.db is not None:
            self._search_engine = CodeSearchEngine(self.db)
        return self._search_engine

    @property
    def parser(self) -> CodeParser:
        if self._parser is None:
            self._parser = CodeParser()
        return self._parser

    def help(self) -> str:
        return (
            "DevAgent Commands:\n"
            "/help - Show this message\n"
            "/status - Show bot status\n"
            "/analyze <path> - Analyze a project directory\n"
            "/index <path> - Index a project for code search\n"
            "/search <query> - Search indexed code\n"
            "/find <name> - Find a definition by name"
        )

    def status(self) -> str:
        return "DevAgent is running. Ready to assist."

    def analyze(self, project_path: str) -> str:
        if not project_path:
            return "Usage: /analyze <path>"
        manifest = self.analyzer.analyze(project_path)
        if manifest.language == "unknown":
            return f"Could not detect project at: {project_path}"
        return (
            f"Project Analysis:\n"
            f"Path: {manifest.path}\n"
            f"{manifest.summary()}\n"
            f"Config files: {', '.join(manifest.config_files)}\n"
            f"Entry points: {', '.join(manifest.entry_points)}"
        )

    async def index(self, project_path: str) -> str:
        """Index a project for code search."""
        if not project_path:
            return "Usage: /index <path>"
        if self.search_engine is None:
            return "Database not available."
        count = await self.search_engine.index_project(project_path, self.parser)
        return f"Indexed {count} entities from: {project_path}"

    async def search(self, query: str, project_path: str = "") -> str:
        """Search indexed code entities."""
        if not query:
            return "Usage: /search <query>"
        if self.search_engine is None:
            return "Database not available."
        results = await self.search_engine.search(query, project_path=project_path or None, limit=10)
        if not results:
            return f"No results found for: {query}"
        lines = [f"Search results for '{query}':"]
        for r in results:
            lines.append(f"  {r.entity_type} {r.entity_name} — {r.file_path}:{r.line}")
        return "\n".join(lines)

    async def find(self, name: str, project_path: str = "") -> str:
        """Find a definition by exact name."""
        if not name:
            return "Usage: /find <name>"
        if self.search_engine is None:
            return "Database not available."
        result = await self.search_engine.find_definition(name, project_path=project_path or None)
        if not result:
            return f"Definition not found: {name}"
        return (
            f"Found: {result['entity_type']} {result['name']}\n"
            f"File: {result['file_path']}:{result['line_start']}\n"
            f"Signature: {result.get('signature', 'N/A')}"
        )
