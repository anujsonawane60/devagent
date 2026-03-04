"""Tests for ValidationRunner and validation dataclasses."""

import json
from unittest.mock import AsyncMock, patch, MagicMock

import pytest

from agent.safety import ValidationCheck, ValidationResult, ValidationRunner


class TestValidationCheck:
    def test_fields(self):
        check = ValidationCheck(name="lint", command=["npm", "run", "lint"], passed=True, output="ok")
        assert check.name == "lint"
        assert check.command == ["npm", "run", "lint"]
        assert check.passed is True
        assert check.output == "ok"

    def test_defaults(self):
        check = ValidationCheck(name="test", command=["pytest"])
        assert check.passed is True
        assert check.output == ""


class TestValidationResult:
    def test_all_passed_true(self):
        checks = [
            ValidationCheck(name="lint", command=["lint"], passed=True),
            ValidationCheck(name="test", command=["test"], passed=True),
        ]
        result = ValidationResult(checks=checks)
        assert result.all_passed is True

    def test_all_passed_false_when_one_fails(self):
        checks = [
            ValidationCheck(name="lint", command=["lint"], passed=True),
            ValidationCheck(name="test", command=["test"], passed=False),
        ]
        result = ValidationResult(checks=checks)
        assert result.all_passed is False

    def test_summary_format(self):
        checks = [
            ValidationCheck(name="lint", command=["lint"], passed=True),
            ValidationCheck(name="test", command=["test"], passed=False),
        ]
        result = ValidationResult(checks=checks)
        summary = result.summary
        assert "1/2 passed" in summary
        assert "[PASS] lint" in summary
        assert "[FAIL] test" in summary
        assert "1 check(s) failed" in summary

    def test_empty_checks(self):
        result = ValidationResult(checks=[])
        assert result.all_passed is True
        assert "0/0 passed" in result.summary


class TestValidationRunner:
    @pytest.mark.asyncio
    async def test_run_check_passing(self, validation_runner):
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"All good\n", None)
        mock_process.returncode = 0

        with patch("agent.safety.asyncio.create_subprocess_exec", return_value=mock_process):
            check = await validation_runner.run_check("lint", ["npm", "run", "lint"])

        assert check.passed is True
        assert check.name == "lint"
        assert "All good" in check.output

    @pytest.mark.asyncio
    async def test_run_check_failing(self, validation_runner):
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"Error found\n", None)
        mock_process.returncode = 1

        with patch("agent.safety.asyncio.create_subprocess_exec", return_value=mock_process):
            check = await validation_runner.run_check("lint", ["npm", "run", "lint"])

        assert check.passed is False
        assert "Error found" in check.output

    @pytest.mark.asyncio
    async def test_run_all_mixed(self, validation_runner):
        call_count = 0

        async def mock_exec(*args, **kwargs):
            nonlocal call_count
            proc = AsyncMock()
            if call_count == 0:
                proc.communicate.return_value = (b"ok", None)
                proc.returncode = 0
            else:
                proc.communicate.return_value = (b"fail", None)
                proc.returncode = 1
            call_count += 1
            return proc

        with patch("agent.safety.asyncio.create_subprocess_exec", side_effect=mock_exec):
            result = await validation_runner.run_all([
                ("lint", ["lint"]),
                ("test", ["test"]),
            ])

        assert len(result.checks) == 2
        assert result.checks[0].passed is True
        assert result.checks[1].passed is False
        assert result.all_passed is False

    @pytest.mark.asyncio
    async def test_run_check_timeout(self, validation_runner):
        import asyncio

        async def mock_exec(*args, **kwargs):
            proc = AsyncMock()
            proc.communicate.side_effect = asyncio.TimeoutError()
            return proc

        with patch("agent.safety.asyncio.create_subprocess_exec", side_effect=mock_exec):
            with patch("agent.safety.asyncio.wait_for", side_effect=asyncio.TimeoutError()):
                check = await validation_runner.run_check("build", ["npm", "run", "build"])

        assert check.passed is False
        assert "Timed out" in check.output or "TimeoutError" in check.output

    def test_detect_checks_package_json(self, tmp_path):
        pkg = {"scripts": {"lint": "eslint .", "test": "jest", "build": "tsc"}}
        (tmp_path / "package.json").write_text(json.dumps(pkg))
        runner = ValidationRunner(str(tmp_path))
        checks = runner.detect_checks()
        names = [c[0] for c in checks]
        assert "lint" in names
        assert "test" in names
        assert "build" in names

    def test_detect_checks_pyproject(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text("[tool.pytest]\n")
        runner = ValidationRunner(str(tmp_path))
        checks = runner.detect_checks()
        names = [c[0] for c in checks]
        assert "lint" in names
        assert "typecheck" in names
        assert "test" in names

    def test_detect_checks_none(self, tmp_path):
        runner = ValidationRunner(str(tmp_path))
        checks = runner.detect_checks()
        assert checks == []
