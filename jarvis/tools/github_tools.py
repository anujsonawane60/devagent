from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig

from jarvis.core.credentials import check_credentials
from jarvis.config import settings

_CRED_CHECK = dict(GITHUB_TOKEN="GitHub personal access token")


def _get_github():
    from github import Github
    return Github(settings.GITHUB_TOKEN)


@tool
async def list_repos(limit: int = 10, *, config: RunnableConfig) -> str:
    """List your GitHub repositories."""
    msg = check_credentials("GitHub", **_CRED_CHECK)
    if msg:
        return msg

    g = _get_github()
    repos = list(g.get_user().get_repos(sort="updated")[:limit])
    if not repos:
        return "No repositories found."

    lines = []
    for r in repos:
        vis = "private" if r.private else "public"
        stars = f" | {r.stargazers_count} stars" if r.stargazers_count else ""
        lines.append(f"- **{r.full_name}** ({vis}){stars}\n  {r.description or 'No description'}")

    return "\n\n".join(lines)


@tool
async def list_prs(repo_name: str, state: str = "open", *, config: RunnableConfig) -> str:
    """List pull requests for a repo. repo_name format: owner/repo. State: open, closed, all."""
    msg = check_credentials("GitHub", **_CRED_CHECK)
    if msg:
        return msg

    g = _get_github()
    repo = g.get_repo(repo_name)
    prs = list(repo.get_pulls(state=state)[:10])
    if not prs:
        return f"No {state} PRs in {repo_name}."

    lines = []
    for pr in prs:
        lines.append(f"- #{pr.number} **{pr.title}** by {pr.user.login} ({pr.state})")

    return "\n".join(lines)


@tool
async def create_issue(repo_name: str, title: str, body: str = "", *, config: RunnableConfig) -> str:
    """Create a GitHub issue. repo_name format: owner/repo."""
    msg = check_credentials("GitHub", **_CRED_CHECK)
    if msg:
        return msg

    g = _get_github()
    repo = g.get_repo(repo_name)
    issue = repo.create_issue(title=title, body=body)
    return f"Issue created: #{issue.number} {title} in {repo_name}"


@tool
async def list_issues(repo_name: str, state: str = "open", *, config: RunnableConfig) -> str:
    """List issues for a repo. repo_name format: owner/repo. State: open, closed, all."""
    msg = check_credentials("GitHub", **_CRED_CHECK)
    if msg:
        return msg

    g = _get_github()
    repo = g.get_repo(repo_name)
    issues = list(repo.get_issues(state=state)[:10])
    if not issues:
        return f"No {state} issues in {repo_name}."

    lines = []
    for issue in issues:
        if not issue.pull_request:  # filter out PRs
            labels = ", ".join(l.name for l in issue.labels) if issue.labels else ""
            label_str = f" [{labels}]" if labels else ""
            lines.append(f"- #{issue.number} **{issue.title}**{label_str} by {issue.user.login}")

    return "\n".join(lines) if lines else f"No {state} issues in {repo_name}."
