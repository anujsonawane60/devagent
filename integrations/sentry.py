"""Sentry integration for real-time error monitoring and autonomous fix generation."""

import logging
from dataclasses import dataclass, field
from typing import List, Optional

import httpx

logger = logging.getLogger(__name__)

API_BASE = "https://sentry.io/api/0"


@dataclass
class SentryFrame:
    """A single stack trace frame."""
    filename: str
    function: str
    lineno: int
    context_line: str = ""
    pre_context: List[str] = field(default_factory=list)
    post_context: List[str] = field(default_factory=list)


@dataclass
class SentryError:
    """A Sentry issue/error with parsed details."""
    issue_id: str
    title: str
    culprit: str
    level: str
    count: int
    first_seen: str
    last_seen: str
    status: str
    error_type: str = ""
    error_value: str = ""
    frames: List[SentryFrame] = field(default_factory=list)
    url: str = ""

    @property
    def summary(self) -> str:
        lines = [f"[{self.level.upper()}] {self.title}"]
        if self.error_type and self.error_value:
            lines.append(f"  {self.error_type}: {self.error_value}")
        lines.append(f"  Culprit: {self.culprit}")
        lines.append(f"  Count: {self.count} | Last: {self.last_seen}")
        if self.frames:
            lines.append(f"  Stack: {self.frames[-1].filename}:{self.frames[-1].lineno}")
        return "\n".join(lines)

    @property
    def fix_context(self) -> str:
        """Generate context string for LLM fix generation."""
        parts = [f"Error: {self.error_type}: {self.error_value}"]
        parts.append(f"Location: {self.culprit}")
        if self.frames:
            parts.append("\nStack trace (most recent last):")
            for frame in self.frames[-5:]:  # Last 5 frames
                parts.append(f"  {frame.filename}:{frame.lineno} in {frame.function}")
                if frame.context_line:
                    parts.append(f"    > {frame.context_line.strip()}")
        return "\n".join(parts)


class SentryClient:
    """Client for Sentry API to fetch and analyze errors."""

    def __init__(self, auth_token: str, org_slug: str, project_slug: str):
        self.auth_token = auth_token
        self.org_slug = org_slug
        self.project_slug = project_slug

    @property
    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.auth_token}"}

    @property
    def _project_url(self) -> str:
        return f"{API_BASE}/projects/{self.org_slug}/{self.project_slug}"

    async def get_issues(self, limit: int = 10, query: str = "is:unresolved") -> List[SentryError]:
        """Fetch recent issues from Sentry."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self._project_url}/issues/",
                headers=self._headers,
                params={"query": query, "limit": limit},
            )
            response.raise_for_status()
            issues = []
            for data in response.json():
                issues.append(SentryError(
                    issue_id=str(data["id"]),
                    title=data.get("title", ""),
                    culprit=data.get("culprit", ""),
                    level=data.get("level", "error"),
                    count=data.get("count", 0),
                    first_seen=data.get("firstSeen", ""),
                    last_seen=data.get("lastSeen", ""),
                    status=data.get("status", ""),
                    url=data.get("permalink", ""),
                ))
            return issues

    async def get_issue_details(self, issue_id: str) -> SentryError:
        """Fetch detailed issue info including stack trace."""
        async with httpx.AsyncClient() as client:
            # Get issue metadata
            issue_resp = await client.get(
                f"{API_BASE}/issues/{issue_id}/",
                headers=self._headers,
            )
            issue_resp.raise_for_status()
            issue_data = issue_resp.json()

            # Get latest event for stack trace
            events_resp = await client.get(
                f"{API_BASE}/issues/{issue_id}/events/latest/",
                headers=self._headers,
            )
            events_resp.raise_for_status()
            event_data = events_resp.json()

            frames = []
            error_type = ""
            error_value = ""

            # Parse exception data from event
            entries = event_data.get("entries", [])
            for entry in entries:
                if entry.get("type") == "exception":
                    exc_data = entry.get("data", {})
                    values = exc_data.get("values", [])
                    if values:
                        exc = values[-1]  # Most recent exception
                        error_type = exc.get("type", "")
                        error_value = exc.get("value", "")
                        stacktrace = exc.get("stacktrace", {})
                        for frame_data in stacktrace.get("frames", []):
                            frames.append(SentryFrame(
                                filename=frame_data.get("filename", ""),
                                function=frame_data.get("function", ""),
                                lineno=frame_data.get("lineNo", 0),
                                context_line=frame_data.get("contextLine", ""),
                                pre_context=frame_data.get("preContext", []),
                                post_context=frame_data.get("postContext", []),
                            ))

            return SentryError(
                issue_id=str(issue_data["id"]),
                title=issue_data.get("title", ""),
                culprit=issue_data.get("culprit", ""),
                level=issue_data.get("level", "error"),
                count=issue_data.get("count", 0),
                first_seen=issue_data.get("firstSeen", ""),
                last_seen=issue_data.get("lastSeen", ""),
                status=issue_data.get("status", ""),
                error_type=error_type,
                error_value=error_value,
                frames=frames,
                url=issue_data.get("permalink", ""),
            )

    async def resolve_issue(self, issue_id: str) -> bool:
        """Mark an issue as resolved."""
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{API_BASE}/issues/{issue_id}/",
                headers=self._headers,
                json={"status": "resolved"},
            )
            return response.status_code == 200
