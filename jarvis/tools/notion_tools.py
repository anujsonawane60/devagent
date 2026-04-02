from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig

from jarvis.core.credentials import check_credentials
from jarvis.config import settings

_CRED_CHECK = dict(NOTION_TOKEN="Notion integration token")


def _get_notion_client():
    from notion_client import Client
    return Client(auth=settings.NOTION_TOKEN)


@tool
async def search_notion(query: str, *, config: RunnableConfig) -> str:
    """Search across all Notion pages and databases shared with the integration."""
    msg = check_credentials("Notion", **_CRED_CHECK)
    if msg:
        return msg

    client = _get_notion_client()
    results = client.search(query=query, page_size=10)

    items = results.get("results", [])
    if not items:
        return f"No Notion pages found for: {query}"

    lines = []
    for item in items:
        obj_type = item["object"]  # "page" or "database"
        if obj_type == "page":
            props = item.get("properties", {})
            # Try to extract title
            title = ""
            for prop in props.values():
                if prop.get("type") == "title" and prop.get("title"):
                    title = prop["title"][0]["plain_text"] if prop["title"] else ""
                    break
            title = title or "(untitled)"
            url = item.get("url", "")
            lines.append(f"- [Page] **{title}**\n  {url}")
        elif obj_type == "database":
            title_list = item.get("title", [])
            title = title_list[0]["plain_text"] if title_list else "(untitled)"
            lines.append(f"- [Database] **{title}**")

    return "\n\n".join(lines)


@tool
async def create_notion_page(title: str, content: str, database_id: str = "", *, config: RunnableConfig) -> str:
    """Create a new Notion page. If database_id is provided, creates within that database.
    Otherwise creates a top-level page."""
    msg = check_credentials("Notion", **_CRED_CHECK)
    if msg:
        return msg

    client = _get_notion_client()

    if database_id:
        # Create in database
        page = client.pages.create(
            parent={"database_id": database_id},
            properties={
                "Name": {"title": [{"text": {"content": title}}]},
            },
            children=[
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": [{"text": {"content": content}}]},
                }
            ],
        )
    else:
        # Create top-level page (requires a parent page — use first available)
        search = client.search(filter={"property": "object", "value": "page"}, page_size=1)
        pages = search.get("results", [])
        if not pages:
            return "No Notion pages found to create under. Share a page with the integration first."

        page = client.pages.create(
            parent={"page_id": pages[0]["id"]},
            properties={
                "title": {"title": [{"text": {"content": title}}]},
            },
            children=[
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": [{"text": {"content": content}}]},
                }
            ],
        )

    return f"Notion page created: {title}\n{page.get('url', '')}"


@tool
async def list_notion_databases(*, config: RunnableConfig) -> str:
    """List all Notion databases shared with the integration."""
    msg = check_credentials("Notion", **_CRED_CHECK)
    if msg:
        return msg

    client = _get_notion_client()
    results = client.search(filter={"property": "object", "value": "database"}, page_size=20)

    items = results.get("results", [])
    if not items:
        return "No Notion databases found. Share a database with the integration first."

    lines = []
    for db in items:
        title_list = db.get("title", [])
        title = title_list[0]["plain_text"] if title_list else "(untitled)"
        db_id = db["id"]
        lines.append(f"- **{title}** (ID: {db_id})")

    return "\n".join(lines)
