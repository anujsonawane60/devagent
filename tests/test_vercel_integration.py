"""Tests for Vercel deployment integration."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from integrations.vercel import VercelClient, Deployment


class TestVercelClientInit:
    def test_init(self, vercel_client):
        assert vercel_client.token == "test-token"
        assert vercel_client.project_id == "prj_test"
        assert vercel_client.team_id == "team_test"

    def test_headers(self, vercel_client):
        assert "Bearer test-token" in vercel_client._headers["Authorization"]

    def test_team_params(self, vercel_client):
        assert vercel_client._team_params == {"teamId": "team_test"}

    def test_no_team_params(self):
        client = VercelClient(token="t", project_id="p")
        assert client._team_params == {}


class TestDeployment:
    def test_deployment_fields(self):
        dep = Deployment(
            id="dpl_123", url="https://test.vercel.app", state="READY",
            target="production", created_at=1700000000, branch="main",
        )
        assert dep.id == "dpl_123"
        assert dep.target == "production"

    def test_status_emoji(self):
        assert Deployment(id="", url="", state="READY", target="", created_at=0).status_emoji == "[OK]"
        assert Deployment(id="", url="", state="ERROR", target="", created_at=0).status_emoji == "[ERR]"
        assert Deployment(id="", url="", state="BUILDING", target="", created_at=0).status_emoji == ">>>"

    def test_summary(self):
        dep = Deployment(
            id="dpl_1", url="https://app.vercel.app", state="READY",
            target="production", created_at=0, branch="main",
        )
        summary = dep.summary
        assert "production" in summary
        assert "READY" in summary
        assert "main" in summary

    def test_summary_with_error(self):
        dep = Deployment(
            id="dpl_1", url="https://app.vercel.app", state="ERROR",
            target="preview", created_at=0, error_message="Build failed",
        )
        assert "Build failed" in dep.summary


class TestCreateDeployment:
    @pytest.mark.asyncio
    async def test_create_deployment(self, vercel_client):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "uid": "dpl_abc123",
            "url": "test-abc.vercel.app",
            "readyState": "QUEUED",
            "target": "preview",
            "createdAt": 1700000000,
            "meta": {"githubCommitRef": "feature-branch"},
        }
        mock_response.raise_for_status = MagicMock()

        with patch("integrations.vercel.httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(return_value=MagicMock(
                post=AsyncMock(return_value=mock_response)
            ))
            mock_client.return_value.__aexit__ = AsyncMock(return_value=False)

            dep = await vercel_client.create_deployment(git_ref="feature-branch")
            assert dep.id == "dpl_abc123"
            assert dep.state == "QUEUED"
            assert dep.branch == "feature-branch"


class TestListDeployments:
    @pytest.mark.asyncio
    async def test_list_deployments(self, vercel_client):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "deployments": [
                {
                    "uid": "dpl_1",
                    "url": "app-1.vercel.app",
                    "readyState": "READY",
                    "target": "production",
                    "createdAt": 1700000000,
                    "meta": {},
                },
                {
                    "uid": "dpl_2",
                    "url": "app-2.vercel.app",
                    "readyState": "READY",
                    "target": "preview",
                    "createdAt": 1699999000,
                    "meta": {},
                },
            ]
        }
        mock_response.raise_for_status = MagicMock()

        with patch("integrations.vercel.httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(return_value=MagicMock(
                get=AsyncMock(return_value=mock_response)
            ))
            mock_client.return_value.__aexit__ = AsyncMock(return_value=False)

            deps = await vercel_client.list_deployments(limit=5)
            assert len(deps) == 2
            assert deps[0].id == "dpl_1"


class TestCancelDeployment:
    @pytest.mark.asyncio
    async def test_cancel(self, vercel_client):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "uid": "dpl_1",
            "url": "app.vercel.app",
            "readyState": "CANCELED",
            "target": "preview",
            "createdAt": 0,
            "meta": {},
        }
        mock_response.raise_for_status = MagicMock()

        with patch("integrations.vercel.httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(return_value=MagicMock(
                patch=AsyncMock(return_value=mock_response)
            ))
            mock_client.return_value.__aexit__ = AsyncMock(return_value=False)

            dep = await vercel_client.cancel_deployment("dpl_1")
            assert dep.state == "CANCELED"


class TestParseDeployment:
    def test_parse_deployment(self, vercel_client):
        data = {
            "uid": "dpl_x",
            "url": "test.vercel.app",
            "readyState": "READY",
            "target": "production",
            "createdAt": 1700000000,
            "meta": {
                "githubCommitRef": "main",
                "githubCommitMessage": "fix: thing",
            },
        }
        dep = vercel_client._parse_deployment(data)
        assert dep.id == "dpl_x"
        assert dep.branch == "main"
        assert dep.commit_message == "fix: thing"

    def test_parse_deployment_minimal(self, vercel_client):
        data = {"uid": "x", "url": "", "readyState": "QUEUED", "createdAt": 0}
        dep = vercel_client._parse_deployment(data)
        assert dep.id == "x"
        assert dep.target == "preview"
