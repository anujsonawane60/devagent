"""Tests for GitHub integration."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from integrations.github import GitHubManager, PullRequest, PRComment


class TestGitHubManagerInit:
    def test_init(self, github_manager):
        assert github_manager.token == "test-token"
        assert github_manager.repo_owner == "testowner"
        assert github_manager.repo_name == "testrepo"

    def test_headers(self, github_manager):
        headers = github_manager._headers
        assert "Bearer test-token" in headers["Authorization"]

    def test_repo_url(self, github_manager):
        assert "testowner/testrepo" in github_manager._repo_url

    def test_set_repo(self, github_manager):
        github_manager.set_repo("newowner", "newrepo")
        assert github_manager.repo_owner == "newowner"
        assert github_manager.repo_name == "newrepo"


class TestDetectRepo:
    def test_detect_ssh_url(self, github_manager):
        result = github_manager.detect_repo_from_remote("git@github.com:owner/repo.git")
        assert result is True
        assert github_manager.repo_owner == "owner"
        assert github_manager.repo_name == "repo"

    def test_detect_https_url(self, github_manager):
        result = github_manager.detect_repo_from_remote("https://github.com/myorg/myrepo.git")
        assert result is True
        assert github_manager.repo_owner == "myorg"
        assert github_manager.repo_name == "myrepo"

    def test_detect_invalid_url(self, github_manager):
        result = github_manager.detect_repo_from_remote("https://gitlab.com/foo/bar")
        assert result is False


class TestPullRequestOperations:
    @pytest.mark.asyncio
    async def test_create_pr(self, github_manager):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "number": 42,
            "title": "Test PR",
            "state": "open",
            "head": {"ref": "feature-branch"},
            "html_url": "https://github.com/testowner/testrepo/pull/42",
            "body": "PR body",
        }
        mock_response.raise_for_status = MagicMock()

        with patch("integrations.github.httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(return_value=MagicMock(
                post=AsyncMock(return_value=mock_response)
            ))
            mock_client.return_value.__aexit__ = AsyncMock(return_value=False)

            pr = await github_manager.create_pull_request(
                title="Test PR", head="feature-branch", base="main", body="PR body"
            )
            assert pr.number == 42
            assert pr.title == "Test PR"
            assert pr.state == "open"
            assert pr.branch == "feature-branch"

    @pytest.mark.asyncio
    async def test_list_prs(self, github_manager):
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "number": 1,
                "title": "First PR",
                "state": "open",
                "head": {"ref": "branch-1"},
                "html_url": "https://github.com/test/test/pull/1",
                "body": "",
            },
            {
                "number": 2,
                "title": "Second PR",
                "state": "open",
                "head": {"ref": "branch-2"},
                "html_url": "https://github.com/test/test/pull/2",
                "body": "",
            },
        ]
        mock_response.raise_for_status = MagicMock()

        with patch("integrations.github.httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(return_value=MagicMock(
                get=AsyncMock(return_value=mock_response)
            ))
            mock_client.return_value.__aexit__ = AsyncMock(return_value=False)

            prs = await github_manager.list_pull_requests()
            assert len(prs) == 2
            assert prs[0].number == 1

    @pytest.mark.asyncio
    async def test_merge_pr(self, github_manager):
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("integrations.github.httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(return_value=MagicMock(
                put=AsyncMock(return_value=mock_response)
            ))
            mock_client.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await github_manager.merge_pull_request(42)
            assert result is True

    @pytest.mark.asyncio
    async def test_add_comment(self, github_manager):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": 123,
            "body": "Test comment",
            "user": {"login": "testuser"},
            "created_at": "2024-01-01T00:00:00Z",
        }
        mock_response.raise_for_status = MagicMock()

        with patch("integrations.github.httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(return_value=MagicMock(
                post=AsyncMock(return_value=mock_response)
            ))
            mock_client.return_value.__aexit__ = AsyncMock(return_value=False)

            comment = await github_manager.add_comment(42, "Test comment")
            assert comment.body == "Test comment"
            assert comment.user == "testuser"


class TestDataclasses:
    def test_pull_request_fields(self):
        pr = PullRequest(number=1, title="Test", state="open", branch="main", url="http://test")
        assert pr.number == 1
        assert pr.mergeable is None

    def test_pr_comment_fields(self):
        comment = PRComment(id=1, body="hi", user="me", created_at="2024-01-01")
        assert comment.id == 1
