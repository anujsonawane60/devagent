"""Tests for ChromaDB semantic search."""

import pytest

from code_engine.embeddings import SemanticSearch, SemanticResult


class TestSemanticSearch:
    def test_init(self, semantic_search):
        assert semantic_search.persist_path is not None
        assert semantic_search._client is None

    def test_index_entities(self, semantic_search):
        entities = [
            {
                "name": "UserService",
                "type": "class",
                "file_path": "src/services/user.py",
                "line_start": 10,
                "signature": "class UserService:",
                "docstring": "Manages user operations",
            },
            {
                "name": "get_user",
                "type": "function",
                "file_path": "src/services/user.py",
                "line_start": 20,
                "signature": "def get_user(user_id: int) -> User",
                "docstring": "Fetch a user by ID",
            },
        ]
        count = semantic_search.index_entities(entities, "test-project")
        assert count == 2

    def test_index_empty(self, semantic_search):
        count = semantic_search.index_entities([], "test-project")
        assert count == 0

    def test_search_after_index(self, semantic_search):
        entities = [
            {
                "name": "AuthController",
                "type": "class",
                "file_path": "src/auth.py",
                "line_start": 5,
                "signature": "class AuthController:",
                "docstring": "Handles authentication and login",
            },
            {
                "name": "calculate_tax",
                "type": "function",
                "file_path": "src/billing.py",
                "line_start": 15,
                "signature": "def calculate_tax(amount: float) -> float",
                "docstring": "Calculate tax for billing",
            },
        ]
        semantic_search.index_entities(entities, "test-project")
        results = semantic_search.search("authentication login", limit=5)
        assert len(results) > 0
        assert isinstance(results[0], SemanticResult)
        # Auth-related result should rank higher
        assert results[0].entity_name == "AuthController"

    def test_search_with_project_filter(self, semantic_search):
        entities = [
            {
                "name": "foo",
                "type": "function",
                "file_path": "src/a.py",
                "line_start": 1,
                "signature": "def foo():",
                "docstring": "A function",
            },
        ]
        semantic_search.index_entities(entities, "project-a")
        results = semantic_search.search("function", project_path="project-a")
        assert len(results) > 0

    def test_search_empty_collection(self, semantic_search):
        results = semantic_search.search("anything")
        assert results == []

    def test_clear_project(self, semantic_search):
        entities = [
            {
                "name": "bar",
                "type": "function",
                "file_path": "src/b.py",
                "line_start": 1,
                "signature": "def bar():",
                "docstring": "",
            },
        ]
        semantic_search.index_entities(entities, "to-clear")
        assert semantic_search.count() > 0
        semantic_search.clear_project("to-clear")
        # After clearing, count should be 0 for that project
        results = semantic_search.search("bar", project_path="to-clear")
        assert len(results) == 0

    def test_count(self, semantic_search):
        assert semantic_search.count() == 0
        entities = [
            {
                "name": "baz",
                "type": "function",
                "file_path": "src/c.py",
                "line_start": 1,
                "signature": "def baz():",
                "docstring": "",
            },
        ]
        semantic_search.index_entities(entities, "count-test")
        assert semantic_search.count() == 1

    def test_entity_id_deterministic(self, semantic_search):
        id1 = semantic_search._entity_id("file.py", "func", 10)
        id2 = semantic_search._entity_id("file.py", "func", 10)
        assert id1 == id2

    def test_semantic_result_fields(self):
        result = SemanticResult(
            entity_name="test",
            entity_type="function",
            file_path="test.py",
            line=10,
            snippet="def test():",
            score=0.95,
        )
        assert result.entity_name == "test"
        assert result.score == 0.95
        assert result.metadata == {}
