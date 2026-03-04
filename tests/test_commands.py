"""Tests for agent/commands.py"""

from pathlib import Path

DUMMY_DATA = Path(__file__).parent / "dummy_data"


class TestCommandHandler:
    def test_help(self, command_handler):
        result = command_handler.help()
        assert "/help" in result
        assert "/status" in result
        assert "/analyze" in result

    def test_status(self, command_handler):
        result = command_handler.status()
        assert "running" in result.lower()

    def test_analyze_valid_project(self, command_handler):
        result = command_handler.analyze(str(DUMMY_DATA / "sample_nextjs_project"))
        assert "nextjs" in result.lower() or "typescript" in result.lower()

    def test_analyze_empty_path(self, command_handler):
        result = command_handler.analyze("")
        assert "Usage" in result

    def test_analyze_nonexistent(self, command_handler):
        result = command_handler.analyze("/nonexistent/path")
        assert "Could not detect" in result
