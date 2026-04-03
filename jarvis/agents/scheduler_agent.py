from datetime import datetime, timezone, timedelta

from jarvis.core.base_agent import AgentDefinition
from jarvis.tools.scheduler_tools import schedule_action, list_schedules, cancel_schedule

# IST = UTC+5:30
IST = timezone(timedelta(hours=5, minutes=30))

SYSTEM_PROMPT_TEMPLATE = """You are a Scheduler specialist agent. You schedule future actions and manage timed events.

Current date and time: {current_datetime} (IST, Asia/Kolkata)

Your capabilities:
- Schedule messages, reminders, and recurring tasks
- List upcoming/past scheduled actions
- Cancel scheduled actions

Guidelines:
- Convert relative times to absolute ISO datetimes using the current date/time above
- All scheduled_at values MUST be in IST (Asia/Kolkata, UTC+05:30) — do NOT convert to UTC
- If the user says "at 11:30 AM", use today's date with that time. If that time has already passed today, use tomorrow's date
- For birthdays: use action_type="send_message" with the contact's name
- For reminders: use action_type="reminder"
- For recurring tasks: use action_type="recurring_task" with recurrence_rule
- Recurrence rules: daily, weekly:mon, weekly:mon,fri, monthly:15, yearly:04-01
- Always confirm the scheduled time clearly to the user"""


def _build_system_prompt() -> str:
    """Build system prompt with the current date/time injected."""
    now = datetime.now(IST)
    return SYSTEM_PROMPT_TEMPLATE.format(
        current_datetime=now.strftime("%Y-%m-%d %H:%M:%S IST (%A)")
    )


def get_agent_definition() -> AgentDefinition:
    return AgentDefinition(
        name="scheduler_agent",
        description="Schedules future actions (send messages, reminders, recurring events). Delegate when the user says 'remind me at...', 'send wishes at...', 'every Monday do...', or anything time-based.",
        system_prompt=_build_system_prompt(),
        tools=[schedule_action, list_schedules, cancel_schedule],
    )
