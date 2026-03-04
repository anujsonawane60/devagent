"""GitHub integration for PR management and repository operations."""

import logging
from dataclasses import dataclass, field
from typing import List, Optional

import httpx

logger = logging.getLogger(__name__)

API_BASE = "https://api.github.com"


@dataclass
class PullRequest:
    """A GitHub pull request."""
    number: int
    title: str
    state: str
    branch: str
    url: str
    body: str = ""
    mergeable: Optional[bool] = None


@dataclass
class PRComment:
    """A comment on a pull request."""
    id: int
    body: str
    user: str
    created_at: str


class GitHubManager:
    """Manages GitHub API interactions for a repository."""

    def __init__(self, token: str, repo_owner: str = "", repo_name: str = ""):
        self.token = token
        self.repo_owner = repo_owner
        self.repo_name = repo_name

    @property
    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    @property
    def _repo_url(self) -> str:
        return f"{API_BASE}/repos/{self.repo_owner}/{self.repo_name}"

    def set_repo(self, owner: str, name: str) -> None:
        """Set the target repository."""
        self.repo_owner = owner
        self.repo_name = name

    def detect_repo_from_remote(self, remote_url: str) -> bool:
        """Parse owner/repo from a git remote URL."""
        # Handle SSH: git@github.com:owner/repo.git
        if "github.com:" in remote_url:
            path = remote_url.split("github.com:")[-1]
            path = path.rstrip(".git")
            parts = path.split("/")
            if len(parts) == 2:
                self.repo_owner, self.repo_name = parts
                return True
        # Handle HTTPS: https://github.com/owner/repo.git
        if "github.com/" in remote_url:
            path = remote_url.split("github.com/")[-1]
            path = path.rstrip(".git")
            parts = path.split("/")
            if len(parts) == 2:
                self.repo_owner, self.repo_name = parts
                return True
        return False

    async def create_pull_request(
        self, title: str, head: str, base: str = "main", body: str = ""
    ) -> PullRequest:
        """Create a new pull request."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self._repo_url}/pulls",
                headers=self._headers,
                json={
                    "title": title,
                    "head": head,
                    "base": base,
                    "body": body,
                },
            )
            response.raise_for_status()
            data = response.json()
            return PullRequest(
                number=data["number"],
                title=data["title"],
                state=data["state"],
                branch=data["head"]["ref"],
                url=data["html_url"],
                body=data.get("body", ""),
            )

    async def list_pull_requests(self, state: str = "open") -> List[PullRequest]:
        """List pull requests for the repository."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self._repo_url}/pulls",
                headers=self._headers,
                params={"state": state, "per_page": 20},
            )
            response.raise_for_status()
            prs = []
            for data in response.json():
                prs.append(PullRequest(
                    number=data["number"],
                    title=data["title"],
                    state=data["state"],
                    branch=data["head"]["ref"],
                    url=data["html_url"],
                    body=data.get("body", ""),
                ))
            return prs

    async def get_pull_request(self, pr_number: int) -> PullRequest:
        """Get details of a specific pull request."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self._repo_url}/pulls/{pr_number}",
                headers=self._headers,
            )
            response.raise_for_status()
            data = response.json()
            return PullRequest(
                number=data["number"],
                title=data["title"],
                state=data["state"],
                branch=data["head"]["ref"],
                url=data["html_url"],
                body=data.get("body", ""),
                mergeable=data.get("mergeable"),
            )

    async def merge_pull_request(
        self, pr_number: int, merge_method: str = "squash"
    ) -> bool:
        """Merge a pull request."""
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{self._repo_url}/pulls/{pr_number}/merge",
                headers=self._headers,
                json={"merge_method": merge_method},
            )
            return response.status_code == 200

    async def add_comment(self, pr_number: int, body: str) -> PRComment:
        """Add a comment to a pull request."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self._repo_url}/issues/{pr_number}/comments",
                headers=self._headers,
                json={"body": body},
            )
            response.raise_for_status()
            data = response.json()
            return PRComment(
                id=data["id"],
                body=data["body"],
                user=data["user"]["login"],
                created_at=data["created_at"],
            )

    async def get_comments(self, pr_number: int) -> List[PRComment]:
        """Get comments on a pull request."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self._repo_url}/issues/{pr_number}/comments",
                headers=self._headers,
            )
            response.raise_for_status()
            comments = []
            for data in response.json():
                comments.append(PRComment(
                    id=data["id"],
                    body=data["body"],
                    user=data["user"]["login"],
                    created_at=data["created_at"],
                ))
            return comments
