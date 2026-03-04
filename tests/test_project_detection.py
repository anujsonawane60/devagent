"""Tests for code_engine/analyzer.py"""

import os
from pathlib import Path

import pytest

from code_engine.analyzer import ProjectAnalyzer, ProjectManifest

DUMMY_DATA = Path(__file__).parent / "dummy_data"


@pytest.fixture
def analyzer():
    return ProjectAnalyzer()


class TestProjectManifest:
    def test_to_dict(self):
        m = ProjectManifest(path="/test", language="python", framework="fastapi")
        d = m.to_dict()
        assert d["language"] == "python"
        assert d["framework"] == "fastapi"

    def test_summary(self):
        m = ProjectManifest(path="/test", language="python", framework="fastapi", dependencies=["fastapi", "uvicorn"])
        s = m.summary()
        assert "python" in s
        assert "fastapi" in s
        assert "2" in s


class TestNextjsDetection:
    def test_detects_language(self, analyzer):
        m = analyzer.analyze(str(DUMMY_DATA / "sample_nextjs_project"))
        assert m.language == "typescript"

    def test_detects_framework(self, analyzer):
        m = analyzer.analyze(str(DUMMY_DATA / "sample_nextjs_project"))
        assert m.framework == "nextjs"

    def test_detects_dependencies(self, analyzer):
        m = analyzer.analyze(str(DUMMY_DATA / "sample_nextjs_project"))
        assert "react" in m.dependencies

    def test_detects_typescript(self, analyzer):
        m = analyzer.analyze(str(DUMMY_DATA / "sample_nextjs_project"))
        assert m.has_typescript is True

    def test_finds_entry_point(self, analyzer):
        m = analyzer.analyze(str(DUMMY_DATA / "sample_nextjs_project"))
        assert "src/app/page.tsx" in m.entry_points


class TestViteDetection:
    def test_detects_framework(self, analyzer):
        m = analyzer.analyze(str(DUMMY_DATA / "sample_vite_project"))
        assert m.framework == "vite"

    def test_detects_config_files(self, analyzer):
        m = analyzer.analyze(str(DUMMY_DATA / "sample_vite_project"))
        assert "vite.config.ts" in m.config_files

    def test_finds_entry_point(self, analyzer):
        m = analyzer.analyze(str(DUMMY_DATA / "sample_vite_project"))
        assert "src/main.tsx" in m.entry_points


class TestPythonDetection:
    def test_detects_language(self, analyzer):
        m = analyzer.analyze(str(DUMMY_DATA / "sample_python_project"))
        assert m.language == "python"

    def test_detects_framework(self, analyzer):
        m = analyzer.analyze(str(DUMMY_DATA / "sample_python_project"))
        assert m.framework == "fastapi"

    def test_detects_dependencies(self, analyzer):
        m = analyzer.analyze(str(DUMMY_DATA / "sample_python_project"))
        assert "fastapi" in m.dependencies

    def test_nonexistent_path(self, analyzer):
        m = analyzer.analyze("/nonexistent/path")
        assert m.language == "unknown"
