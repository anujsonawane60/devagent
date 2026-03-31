from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig

from jarvis.db.repositories import ScheduledJobRepo
from jarvis.tools import get_user_context


@tool
async def schedule_action(
    action_type: str,
    description: str,
    scheduled_at: str,
    message: str = "",
    contact_name: str = "",
    recurrence_rule: str = "",
    *,
    config: RunnableConfig,
) -> str:
    """Schedule a future action. action_type can be: send_message, reminder, recurring_task.
    scheduled_at format: YYYY-MM-DDTHH:MM:SS (e.g., 2026-04-01T00:00:00).
    recurrence_rule: daily, weekly:mon, weekly:mon,fri, monthly:15, yearly:04-01."""
    ctx = get_user_context(config)

    payload = {}
    if message:
        payload["message"] = message
    if contact_name:
        payload["contact_name"] = contact_name

    # Look up contact ID if name provided
    target_contact_id = None
    if contact_name:
        from jarvis.db.repositories import ContactRepo
        contact = await ContactRepo.find_by_name(ctx.user_id, contact_name)
        if contact:
            target_contact_id = contact["id"]

    job_id = await ScheduledJobRepo.create(
        user_id=ctx.user_id,
        action_type=action_type,
        description=description,
        payload=payload,
        target_contact_id=target_contact_id,
        scheduled_at=scheduled_at,
        recurrence_rule=recurrence_rule or None,
    )
    recur = f" (recurring: {recurrence_rule})" if recurrence_rule else ""
    return f"Scheduled #{job_id}: {description} at {scheduled_at}{recur}"


@tool
async def list_schedules(status: str = "pending", *, config: RunnableConfig) -> str:
    """List scheduled actions. Status can be: pending, completed, failed, cancelled, or empty for all."""
    ctx = get_user_context(config)
    jobs = await ScheduledJobRepo.list_jobs(ctx.user_id, status=status or None)
    if not jobs:
        return f"No {status + ' ' if status else ''}scheduled actions."
    lines = []
    for j in jobs:
        recur = f" | recurring: {j['recurrence_rule']}" if j.get("recurrence_rule") else ""
        target = f" | contact: {j['payload'].get('contact_name', '')}" if j["payload"].get("contact_name") else ""
        lines.append(f"#{j['id']} [{j['status']}] {j['description']} | at: {j['scheduled_at']}{recur}{target}")
    return "\n".join(lines)


@tool
async def cancel_schedule(job_id: int, *, config: RunnableConfig) -> str:
    """Cancel a scheduled action by its ID."""
    ctx = get_user_context(config)
    success = await ScheduledJobRepo.cancel(ctx.user_id, job_id)
    if not success:
        return f"Schedule #{job_id} not found or already completed."
    return f"Schedule #{job_id} cancelled."
