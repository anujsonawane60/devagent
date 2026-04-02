from jarvis.core.base_agent import AgentDefinition
from jarvis.tools.github_tools import list_repos, list_prs, create_issue, list_issues

SYSTEM_PROMPT = """You are a GitHub specialist agent. You interact with the user's GitHub account.

Your capabilities:
- List repositories
- List pull requests for a repo
- Create issues
- List issues

Guidelines:
- Repo names are in owner/repo format (e.g., "anujsonawane60/devagent")
- If the user doesn't specify a repo, ask them which one
- Present PR/issue info clearly with numbers, titles, and authors"""


def get_agent_definition() -> AgentDefinition:
    return AgentDefinition(
        name="github_agent",
        description="Interacts with GitHub — repos, PRs, issues. Delegate when the user asks about their code repositories, pull requests, or wants to create an issue.",
        system_prompt=SYSTEM_PROMPT,
        tools=[list_repos, list_prs, create_issue, list_issues],
    )
