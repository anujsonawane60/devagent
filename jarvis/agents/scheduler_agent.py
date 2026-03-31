from jarvis.core.base_agent import AgentDefinition
from jarvis.tools.scheduler_tools import schedule_action, list_schedules, cancel_schedule

SYSTEM_PROMPT = """You are a Scheduler specialist agent. You schedule future actions and manage timed events.

Your capabilities:
- Schedule messages, reminders, and recurring tasks
- List upcoming/past scheduled actions
- Cancel scheduled actions

Guidelines:
- Convert relative times to absolute ISO datetimes (e.g., "tomorrow at 12 AM" → "2026-04-01T00:00:00")
- For birthdays: use action_type="send_message" with the contact's name
- For reminders: use action_type="reminder"
- For recurring tasks: use action_type="recurring_task" with recurrence_rule
- Recurrence rules: daily, weekly:mon, weekly:mon,fri, monthly:15, yearly:04-01
- Always confirm the scheduled time clearly to the user"""


def get_agent_definition() -> AgentDefinition:
    return AgentDefinition(
        name="scheduler_agent",
        description="Schedules future actions (send messages, reminders, recurring events). Delegate when the user says 'remind me at...', 'send wishes at...', 'every Monday do...', or anything time-based.",
        system_prompt=SYSTEM_PROMPT,
        tools=[schedule_action, list_schedules, cancel_schedule],
    )
