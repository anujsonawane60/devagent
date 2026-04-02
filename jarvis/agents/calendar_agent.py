from jarvis.core.base_agent import AgentDefinition
from jarvis.tools.calendar_tools import list_events, create_event, check_availability

SYSTEM_PROMPT = """You are a Calendar specialist agent. You manage the user's Google Calendar.

Your capabilities:
- List upcoming events
- Create new events with time, location, description
- Check availability on a specific date

Guidelines:
- Convert relative times to ISO format (e.g., "tomorrow at 3pm" → "2026-04-01T15:00:00")
- If the user doesn't specify end time, default to 1 hour
- Always confirm the event details before creating
- Present schedule in a clean, chronological format"""


def get_agent_definition() -> AgentDefinition:
    return AgentDefinition(
        name="calendar_agent",
        description="Manages Google Calendar — create events, check schedule, find free slots. Delegate when the user asks about their schedule, wants to create a meeting, or check availability.",
        system_prompt=SYSTEM_PROMPT,
        tools=[list_events, create_event, check_availability],
    )
