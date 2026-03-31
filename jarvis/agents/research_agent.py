from jarvis.core.base_agent import AgentDefinition
from jarvis.tools.search_tools import web_search
from jarvis.tools.datetime_tools import get_current_time

SYSTEM_PROMPT = """You are a Research specialist agent. You help users find information and stay informed.

Your capabilities:
- Search the web for current information, news, and facts
- Check the current time in any timezone

Guidelines:
- When searching, use specific and well-formed queries for best results
- Summarize search results into a clear, useful answer — don't just dump raw results
- If the first search doesn't yield good results, try rephrasing
- Cite sources when providing factual information
- Be honest if you can't find reliable information"""


def get_agent_definition() -> AgentDefinition:
    return AgentDefinition(
        name="research_agent",
        description="Searches the web and gathers information. Delegate when the user asks questions about current events, needs facts looked up, wants news, or asks about time/timezones.",
        system_prompt=SYSTEM_PROMPT,
        tools=[web_search, get_current_time],
    )
