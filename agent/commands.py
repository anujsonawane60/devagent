"""Business logic for bot commands."""

from code_engine.analyzer import ProjectAnalyzer


class CommandHandler:
    def __init__(self, analyzer: ProjectAnalyzer | None = None):
        self.analyzer = analyzer or ProjectAnalyzer()

    def help(self) -> str:
        return (
            "DevAgent Commands:\n"
            "/help - Show this message\n"
            "/status - Show bot status\n"
            "/analyze <path> - Analyze a project directory"
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
