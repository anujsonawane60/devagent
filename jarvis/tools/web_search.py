from langchain_core.tools import tool
from duckduckgo_search import DDGS


@tool
def web_search(query: str, max_results: int = 5) -> str:
    """Search the web for current information. Use this when the user asks about recent events, facts, or anything you're unsure about."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        if not results:
            return "No results found."
        lines = []
        for i, r in enumerate(results, 1):
            lines.append(f"{i}. **{r['title']}**\n   {r['body']}\n   {r['href']}")
        return "\n\n".join(lines)
    except Exception as e:
        return f"Search failed: {str(e)}"
