"""Project detection and analysis."""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class ProjectManifest:
    path: str
    language: str = "unknown"
    framework: str = "unknown"
    dependencies: List[str] = field(default_factory=list)
    dev_dependencies: List[str] = field(default_factory=list)
    has_typescript: bool = False
    entry_points: List[str] = field(default_factory=list)
    config_files: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "language": self.language,
            "framework": self.framework,
            "dependencies": self.dependencies,
            "dev_dependencies": self.dev_dependencies,
            "has_typescript": self.has_typescript,
            "entry_points": self.entry_points,
            "config_files": self.config_files,
        }

    def summary(self) -> str:
        parts = [f"Language: {self.language}", f"Framework: {self.framework}"]
        if self.has_typescript:
            parts.append("TypeScript: yes")
        if self.dependencies:
            parts.append(f"Dependencies: {len(self.dependencies)}")
        return " | ".join(parts)


class ProjectAnalyzer:
    """Detects project type, language, framework, and dependencies."""

    FRAMEWORK_INDICATORS = {
        "next": "nextjs",
        "nuxt": "nuxt",
        "vite": "vite",
        "gatsby": "gatsby",
        "express": "express",
        "fastapi": "fastapi",
        "django": "django",
        "flask": "flask",
    }

    def analyze(self, project_path: str) -> ProjectManifest:
        path = Path(project_path)
        manifest = ProjectManifest(path=project_path)

        if not path.exists():
            return manifest

        # Detect config files
        manifest.config_files = self._find_config_files(path)

        # Detect language and framework
        if (path / "package.json").exists():
            self._analyze_node_project(path, manifest)
        elif (path / "requirements.txt").exists() or (path / "setup.py").exists() or (path / "pyproject.toml").exists():
            self._analyze_python_project(path, manifest)

        # Detect TypeScript
        manifest.has_typescript = (path / "tsconfig.json").exists()

        # Detect entry points
        manifest.entry_points = self._find_entry_points(path)

        return manifest

    def _analyze_node_project(self, path: Path, manifest: ProjectManifest) -> None:
        manifest.language = "javascript"
        if manifest.has_typescript or (path / "tsconfig.json").exists():
            manifest.language = "typescript"

        try:
            with open(path / "package.json") as f:
                pkg = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return

        deps = list(pkg.get("dependencies", {}).keys())
        dev_deps = list(pkg.get("devDependencies", {}).keys())
        manifest.dependencies = deps
        manifest.dev_dependencies = dev_deps

        all_deps = deps + dev_deps
        for dep_name, framework in self.FRAMEWORK_INDICATORS.items():
            if any(dep_name in d for d in all_deps):
                manifest.framework = framework
                break

    def _analyze_python_project(self, path: Path, manifest: ProjectManifest) -> None:
        manifest.language = "python"

        if (path / "requirements.txt").exists():
            with open(path / "requirements.txt") as f:
                deps = [line.split("==")[0].split(">=")[0].split("<=")[0].strip()
                        for line in f if line.strip() and not line.startswith("#")]
                manifest.dependencies = deps

        for dep_name, framework in self.FRAMEWORK_INDICATORS.items():
            if dep_name in manifest.dependencies:
                manifest.framework = framework
                break

    def _find_config_files(self, path: Path) -> List[str]:
        config_patterns = [
            "package.json", "tsconfig.json", "next.config.js", "next.config.mjs",
            "vite.config.ts", "vite.config.js", "pyproject.toml", "setup.py",
            "setup.cfg", "requirements.txt", ".env", ".eslintrc.js", ".prettierrc",
        ]
        found = []
        for pattern in config_patterns:
            if (path / pattern).exists():
                found.append(pattern)
        return found

    def _find_entry_points(self, path: Path) -> List[str]:
        entry_patterns = [
            "src/app/page.tsx", "src/app/page.js",
            "src/main.tsx", "src/main.ts", "src/main.js",
            "src/index.tsx", "src/index.ts", "src/index.js",
            "app/main.py", "main.py", "app.py",
        ]
        found = []
        for pattern in entry_patterns:
            if (path / pattern).exists():
                found.append(pattern)
        return found
