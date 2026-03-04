"""Vercel deployment integration for staging/production deployments."""

import logging
from dataclasses import dataclass
from typing import List, Optional

import httpx

logger = logging.getLogger(__name__)

API_BASE = "https://api.vercel.com"


@dataclass
class Deployment:
    """A Vercel deployment."""
    id: str
    url: str
    state: str  # QUEUED, BUILDING, READY, ERROR, CANCELED
    target: str  # production, preview
    created_at: int
    branch: str = ""
    commit_message: str = ""
    error_message: str = ""

    @property
    def status_emoji(self) -> str:
        return {
            "QUEUED": "...",
            "BUILDING": ">>>",
            "READY": "[OK]",
            "ERROR": "[ERR]",
            "CANCELED": "[X]",
        }.get(self.state, "?")

    @property
    def summary(self) -> str:
        lines = [f"{self.status_emoji} {self.target}: {self.url}"]
        if self.branch:
            lines[0] += f" ({self.branch})"
        lines.append(f"  State: {self.state}")
        if self.error_message:
            lines.append(f"  Error: {self.error_message}")
        return "\n".join(lines)


class VercelClient:
    """Client for Vercel deployment API."""

    def __init__(self, token: str, project_id: str = "", team_id: str = ""):
        self.token = token
        self.project_id = project_id
        self.team_id = team_id

    @property
    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.token}"}

    @property
    def _team_params(self) -> dict:
        if self.team_id:
            return {"teamId": self.team_id}
        return {}

    async def create_deployment(
        self,
        git_ref: str,
        target: str = "preview",
        project_name: Optional[str] = None,
    ) -> Deployment:
        """Trigger a new deployment via the Vercel API."""
        payload = {
            "name": project_name or self.project_id,
            "target": target,
            "gitSource": {
                "ref": git_ref,
                "type": "branch",
            },
        }
        if self.project_id:
            payload["project"] = self.project_id

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE}/v13/deployments",
                headers=self._headers,
                params=self._team_params,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return self._parse_deployment(data)

    async def get_deployment(self, deployment_id: str) -> Deployment:
        """Get the status of a specific deployment."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE}/v13/deployments/{deployment_id}",
                headers=self._headers,
                params=self._team_params,
            )
            response.raise_for_status()
            return self._parse_deployment(response.json())

    async def list_deployments(self, limit: int = 10, target: Optional[str] = None) -> List[Deployment]:
        """List recent deployments."""
        params = {**self._team_params, "limit": limit}
        if self.project_id:
            params["projectId"] = self.project_id
        if target:
            params["target"] = target

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE}/v6/deployments",
                headers=self._headers,
                params=params,
            )
            response.raise_for_status()
            deployments = []
            for data in response.json().get("deployments", []):
                deployments.append(self._parse_deployment(data))
            return deployments

    async def cancel_deployment(self, deployment_id: str) -> Deployment:
        """Cancel a running deployment."""
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"{API_BASE}/v12/deployments/{deployment_id}/cancel",
                headers=self._headers,
                params=self._team_params,
            )
            response.raise_for_status()
            return self._parse_deployment(response.json())

    async def promote_to_production(self, deployment_id: str) -> Deployment:
        """Promote a preview deployment to production."""
        async with httpx.AsyncClient() as client:
            # Create alias to production
            response = await client.post(
                f"{API_BASE}/v10/projects/{self.project_id}/promote/{deployment_id}",
                headers=self._headers,
                params=self._team_params,
            )
            response.raise_for_status()
            # Return updated deployment
            return await self.get_deployment(deployment_id)

    async def rollback(self, target: str = "production") -> Deployment:
        """Rollback to the previous successful deployment."""
        deployments = await self.list_deployments(limit=10, target=target)
        ready = [d for d in deployments if d.state == "READY"]
        if len(ready) < 2:
            raise ValueError(f"No previous {target} deployment to rollback to.")
        # Skip current (index 0), promote previous (index 1)
        previous = ready[1]
        return await self.promote_to_production(previous.id)

    def _parse_deployment(self, data: dict) -> Deployment:
        """Parse API response into a Deployment dataclass."""
        meta = data.get("meta", {})
        git_meta = meta if isinstance(meta, dict) else {}
        error_msg = ""
        if data.get("errorMessage"):
            error_msg = data["errorMessage"]

        return Deployment(
            id=data.get("uid", data.get("id", "")),
            url=f"https://{data.get('url', '')}",
            state=data.get("readyState", data.get("state", "UNKNOWN")),
            target=data.get("target", "preview") or "preview",
            created_at=data.get("createdAt", data.get("created", 0)),
            branch=git_meta.get("githubCommitRef", git_meta.get("gitlabCommitRef", "")),
            commit_message=git_meta.get("githubCommitMessage", git_meta.get("gitlabCommitMessage", "")),
            error_message=error_msg,
        )
