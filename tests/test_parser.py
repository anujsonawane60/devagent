"""Tests for code_engine/parser.py — ~12 tests."""

import os
from pathlib import Path

import pytest

from code_engine.parser import CodeParser, CodeEntity, FileParseResult

DUMMY_DATA = Path(__file__).parent / "dummy_data"


class TestParsePython:
    def test_parse_function(self, parser):
        source = 'def greet(name: str) -> str:\n    """Say hello."""\n    return f"Hello {name}"'
        result = parser.parse_python(source, "test.py")
        assert len(result.entities) == 1
        e = result.entities[0]
        assert e.name == "greet"
        assert e.type == "function"
        assert e.signature == "def greet(name: str) -> str"
        assert e.docstring == "Say hello."

    def test_parse_class_and_methods(self, parser):
        source = (
            'class User:\n'
            '    """A user."""\n'
            '    def __init__(self, name):\n'
            '        self.name = name\n'
            '    def greet(self):\n'
            '        return self.name\n'
        )
        result = parser.parse_python(source, "test.py")
        types = [(e.name, e.type) for e in result.entities]
        assert ("User", "class") in types
        assert ("__init__", "method") in types
        assert ("greet", "method") in types
        # Check class docstring
        cls = [e for e in result.entities if e.name == "User"][0]
        assert cls.docstring == "A user."

    def test_parse_imports(self, parser):
        source = "import os\nfrom pathlib import Path\n\ndef foo(): pass"
        result = parser.parse_python(source, "test.py")
        assert len(result.imports) == 2
        assert "import os" in result.imports
        assert "from pathlib import Path" in result.imports

    def test_parse_decorated_function(self, parser):
        source = "@app.get('/')\ndef index():\n    pass"
        result = parser.parse_python(source, "test.py")
        assert len(result.entities) == 1
        assert result.entities[0].name == "index"

    def test_parse_models_file(self, parser):
        result = parser.parse_file(str(DUMMY_DATA / "sample_python_project" / "app" / "models.py"))
        names = [e.name for e in result.entities]
        assert "User" in names
        assert "Project" in names
        assert "create_user" in names
        assert "full_name" in names

    def test_parse_utils_file(self, parser):
        result = parser.parse_file(str(DUMMY_DATA / "sample_python_project" / "app" / "utils.py"))
        names = [e.name for e in result.entities]
        assert "read_json" in names
        assert "FileProcessor" in names
        assert "list_files" in names


class TestParseJavaScriptTypeScript:
    def test_parse_js_function(self, parser):
        source = "function fetchData(url) {\n  return fetch(url)\n}"
        result = parser.parse_javascript(source, "test.js")
        assert len(result.entities) == 1
        assert result.entities[0].name == "fetchData"
        assert result.entities[0].type == "function"

    def test_parse_arrow_function(self, parser):
        source = "const formatError = (error) => {\n  return error.message\n}"
        result = parser.parse_javascript(source, "test.js")
        assert len(result.entities) == 1
        assert result.entities[0].name == "formatError"
        assert result.entities[0].type == "function"

    def test_parse_react_component(self, parser):
        result = parser.parse_file(str(DUMMY_DATA / "sample_nextjs_project" / "src" / "app" / "layout.tsx"))
        names = [e.name for e in result.entities]
        types = {e.name: e.type for e in result.entities}
        assert "RootLayout" in names
        assert types["RootLayout"] == "component"

    def test_parse_ts_exports(self, parser):
        result = parser.parse_file(str(DUMMY_DATA / "sample_nextjs_project" / "src" / "lib" / "api.ts"))
        assert len(result.exports) > 0
        assert "fetchUsers" in result.exports

    def test_parse_ts_imports(self, parser):
        result = parser.parse_file(str(DUMMY_DATA / "sample_nextjs_project" / "src" / "lib" / "api.ts"))
        assert len(result.imports) > 0
        assert any("types" in imp for imp in result.imports)


class TestParseProject:
    def test_parse_python_project(self, parser):
        results = parser.parse_project(str(DUMMY_DATA / "sample_python_project"))
        assert len(results) >= 2  # at least models.py and utils.py
        all_entities = [e for r in results for e in r.entities]
        assert len(all_entities) >= 10

    def test_parse_nextjs_project(self, parser):
        results = parser.parse_project(str(DUMMY_DATA / "sample_nextjs_project"))
        assert len(results) >= 2  # layout.tsx, api.ts, page.tsx
        languages = {r.language for r in results}
        assert "typescript" in languages

    def test_skip_binary_files(self, parser):
        result = parser.parse_file("test.png")
        assert result is None

    def test_unsupported_extension(self, parser):
        result = parser.parse_file("test.md")
        assert result is None

    def test_syntax_error_graceful(self, parser):
        # tree-sitter still returns partial results on invalid syntax
        source = "def broken(\n    pass  # missing colon"
        result = parser.parse_python(source, "broken.py")
        assert isinstance(result, FileParseResult)
