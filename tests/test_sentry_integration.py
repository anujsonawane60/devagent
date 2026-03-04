"""Tests for Sentry integration."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from integrations.sentry import SentryClient, SentryError, SentryFrame


class TestSentryClientInit:
    def test_init(self, sentry_client):
        assert sentry_client.auth_token == "test-token"
        assert sentry_client.org_slug == "test-org"
        assert sentry_client.project_slug == "test-project"

    def test_headers(self, sentry_client):
        assert "Bearer test-token" in sentry_client._headers["Authorization"]

    def test_project_url(self, sentry_client):
        assert "test-org/test-project" in sentry_client._project_url


class TestGetIssues:
    @pytest.mark.asyncio
    async def test_get_issues(self, sentry_client):
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "id": "12345",
                "title": "TypeError: Cannot read property 'x'",
                "culprit": "src/app.js",
                "level": "error",
                "count": 42,
                "firstSeen": "2024-01-01T00:00:00Z",
                "lastSeen": "2024-01-02T00:00:00Z",
                "status": "unresolved",
                "permalink": "https://sentry.io/issue/12345",
            },
        ]
        mock_response.raise_for_status = MagicMock()

        with patch("integrations.sentry.httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(return_value=MagicMock(
                get=AsyncMock(return_value=mock_response)
            ))
            mock_client.return_value.__aexit__ = AsyncMock(return_value=False)

            issues = await sentry_client.get_issues(limit=5)
            assert len(issues) == 1
            assert issues[0].issue_id == "12345"
            assert issues[0].title == "TypeError: Cannot read property 'x'"
            assert issues[0].count == 42

    @pytest.mark.asyncio
    async def test_get_issues_empty(self, sentry_client):
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status = MagicMock()

        with patch("integrations.sentry.httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(return_value=MagicMock(
                get=AsyncMock(return_value=mock_response)
            ))
            mock_client.return_value.__aexit__ = AsyncMock(return_value=False)

            issues = await sentry_client.get_issues()
            assert issues == []


class TestGetIssueDetails:
    @pytest.mark.asyncio
    async def test_get_issue_details_with_stack_trace(self, sentry_client):
        issue_response = MagicMock()
        issue_response.json.return_value = {
            "id": "12345",
            "title": "ValueError",
            "culprit": "src/handler.py",
            "level": "error",
            "count": 10,
            "firstSeen": "2024-01-01",
            "lastSeen": "2024-01-02",
            "status": "unresolved",
            "permalink": "https://sentry.io/12345",
        }
        issue_response.raise_for_status = MagicMock()

        event_response = MagicMock()
        event_response.json.return_value = {
            "entries": [
                {
                    "type": "exception",
                    "data": {
                        "values": [
                            {
                                "type": "ValueError",
                                "value": "invalid input",
                                "stacktrace": {
                                    "frames": [
                                        {
                                            "filename": "src/handler.py",
                                            "function": "process",
                                            "lineNo": 42,
                                            "contextLine": "    raise ValueError('invalid input')",
                                            "preContext": ["    if not valid:"],
                                            "postContext": [""],
                                        }
                                    ]
                                },
                            }
                        ]
                    },
                }
            ]
        }
        event_response.raise_for_status = MagicMock()

        mock_http = MagicMock()
        mock_http.get = AsyncMock(side_effect=[issue_response, event_response])

        with patch("integrations.sentry.httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_http)
            mock_client.return_value.__aexit__ = AsyncMock(return_value=False)

            error = await sentry_client.get_issue_details("12345")
            assert error.error_type == "ValueError"
            assert error.error_value == "invalid input"
            assert len(error.frames) == 1
            assert error.frames[0].filename == "src/handler.py"
            assert error.frames[0].lineno == 42


class TestResolveIssue:
    @pytest.mark.asyncio
    async def test_resolve(self, sentry_client):
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("integrations.sentry.httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(return_value=MagicMock(
                put=AsyncMock(return_value=mock_response)
            ))
            mock_client.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await sentry_client.resolve_issue("12345")
            assert result is True


class TestDataclasses:
    def test_sentry_frame_fields(self):
        frame = SentryFrame(filename="app.py", function="main", lineno=10, context_line="x = 1")
        assert frame.filename == "app.py"
        assert frame.pre_context == []

    def test_sentry_error_summary(self):
        error = SentryError(
            issue_id="1",
            title="TestError",
            culprit="test.py",
            level="error",
            count=5,
            first_seen="2024-01-01",
            last_seen="2024-01-02",
            status="unresolved",
            error_type="TypeError",
            error_value="bad type",
        )
        summary = error.summary
        assert "TestError" in summary
        assert "TypeError" in summary
        assert "Count: 5" in summary

    def test_sentry_error_fix_context(self):
        error = SentryError(
            issue_id="1",
            title="TestError",
            culprit="test.py",
            level="error",
            count=1,
            first_seen="",
            last_seen="",
            status="unresolved",
            error_type="KeyError",
            error_value="'name'",
            frames=[
                SentryFrame(filename="app.py", function="handler", lineno=25, context_line="x = data['name']"),
            ],
        )
        ctx = error.fix_context
        assert "KeyError" in ctx
        assert "app.py:25" in ctx
        assert "handler" in ctx
