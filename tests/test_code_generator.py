"""Tests for code_engine/generator.py"""

import json
import os

import pytest

from code_engine.generator import (
    CodeGenerator,
    FileChange,
    GenerationPlan,
    GenerationResult,
)
from config.llm import LLMResponse


class TestDataclasses:
    def test_file_change_fields(self):
        fc = FileChange(file_path="a.py", action="create", content="x=1", description="add a")
        assert fc.file_path == "a.py"
        assert fc.action == "create"
        assert fc.content == "x=1"
        assert fc.description == "add a"

    def test_generation_plan_fields(self):
        plan = GenerationPlan(task="do stuff", changes=[], summary="nothing")
        assert plan.task == "do stuff"
        assert plan.changes == []
        assert plan.summary == "nothing"

    def test_generation_result_defaults(self):
        plan = GenerationPlan(task="t")
        result = GenerationResult(plan=plan)
        assert result.success is True
        assert result.error is None


class TestPromptBuilding:
    def test_system_prompt_includes_project(self, mock_llm):
        gen = CodeGenerator(mock_llm)
        prompt = gen._build_system_prompt("/path/to/myproject", "")
        assert "myproject" in prompt
        assert "senior developer" in prompt.lower()

    def test_system_prompt_includes_context(self, mock_llm):
        gen = CodeGenerator(mock_llm)
        prompt = gen._build_system_prompt("/proj", "some relevant code here")
        assert "some relevant code here" in prompt

    def test_generation_prompt_includes_task(self, mock_llm):
        gen = CodeGenerator(mock_llm)
        prompt = gen._build_generation_prompt("add login page", "")
        assert "add login page" in prompt
        assert "JSON" in prompt


class TestResponseParsing:
    def test_parse_valid_json(self, mock_llm):
        gen = CodeGenerator(mock_llm)
        response = json.dumps({
            "changes": [
                {"file_path": "app.py", "action": "create", "content": "print('hi')", "description": "main file"}
            ],
            "summary": "created app"
        })
        changes = gen._parse_llm_response(response)
        assert len(changes) == 1
        assert changes[0].file_path == "app.py"
        assert changes[0].action == "create"
        assert changes[0].content == "print('hi')"

    def test_parse_json_with_code_fences(self, mock_llm):
        gen = CodeGenerator(mock_llm)
        response = '```json\n{"changes": [{"file_path": "x.py", "action": "modify", "content": "pass"}], "summary": "ok"}\n```'
        changes = gen._parse_llm_response(response)
        assert len(changes) == 1
        assert changes[0].file_path == "x.py"

    def test_parse_malformed_response(self, mock_llm):
        gen = CodeGenerator(mock_llm)
        changes = gen._parse_llm_response("this is not json at all")
        assert changes == []

    def test_parse_missing_fields(self, mock_llm):
        gen = CodeGenerator(mock_llm)
        response = json.dumps({"changes": [{"file_path": "a.py"}]})
        changes = gen._parse_llm_response(response)
        assert changes == []  # missing action


class TestApplyPlan:
    def test_create_file(self, mock_llm, tmp_path):
        gen = CodeGenerator(mock_llm)
        plan = GenerationPlan(
            task="create",
            changes=[FileChange(file_path="new.py", action="create", content="x = 1")],
        )
        result = gen.apply_plan(plan, str(tmp_path))
        assert result.success
        assert (tmp_path / "new.py").read_text() == "x = 1"

    def test_modify_file(self, mock_llm, tmp_path):
        gen = CodeGenerator(mock_llm)
        (tmp_path / "exist.py").write_text("old")
        plan = GenerationPlan(
            task="modify",
            changes=[FileChange(file_path="exist.py", action="modify", content="new")],
        )
        result = gen.apply_plan(plan, str(tmp_path))
        assert result.success
        assert (tmp_path / "exist.py").read_text() == "new"

    def test_delete_file(self, mock_llm, tmp_path):
        gen = CodeGenerator(mock_llm)
        (tmp_path / "gone.py").write_text("bye")
        plan = GenerationPlan(
            task="delete",
            changes=[FileChange(file_path="gone.py", action="delete")],
        )
        result = gen.apply_plan(plan, str(tmp_path))
        assert result.success
        assert not (tmp_path / "gone.py").exists()

    def test_create_nested_file(self, mock_llm, tmp_path):
        gen = CodeGenerator(mock_llm)
        plan = GenerationPlan(
            task="create nested",
            changes=[FileChange(file_path="sub/dir/app.py", action="create", content="ok")],
        )
        result = gen.apply_plan(plan, str(tmp_path))
        assert result.success
        assert (tmp_path / "sub" / "dir" / "app.py").read_text() == "ok"


class TestGeneratePlan:
    @pytest.mark.asyncio
    async def test_generate_plan_end_to_end(self, mock_llm):
        mock_llm.generate.return_value = LLMResponse(
            content=json.dumps({
                "changes": [
                    {"file_path": "hello.py", "action": "create", "content": "print('hello')", "description": "greeting"}
                ],
                "summary": "Added greeting"
            }),
            model="mock",
            usage={"input_tokens": 5, "output_tokens": 10},
        )
        gen = CodeGenerator(mock_llm)
        plan = await gen.generate_plan("add a greeting", "/fake/path")
        assert len(plan.changes) == 1
        assert plan.changes[0].file_path == "hello.py"
        assert plan.task == "add a greeting"
        mock_llm.generate.assert_called_once()
