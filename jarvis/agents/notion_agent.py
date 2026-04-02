from jarvis.core.base_agent import AgentDefinition
from jarvis.tools.notion_tools import search_notion, create_notion_page, list_notion_databases

SYSTEM_PROMPT = """You are a Notion specialist agent. You interact with the user's Notion workspace.

Your capabilities:
- Search across all shared Notion pages and databases
- Create new pages (in a database or as top-level)
- List available databases

Guidelines:
- When creating a page in a database, you need the database_id — use list_notion_databases to find it
- Format content clearly — Notion supports rich text
- If the user says "add to Notion", search for the relevant database first"""


def get_agent_definition() -> AgentDefinition:
    return AgentDefinition(
        name="notion_agent",
        description="Interacts with Notion — search pages, create pages, list databases. Delegate when the user mentions Notion or wants to save/find something in their Notion workspace.",
        system_prompt=SYSTEM_PROMPT,
        tools=[search_notion, create_notion_page, list_notion_databases],
    )
