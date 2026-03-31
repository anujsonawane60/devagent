from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig

from jarvis.db.repositories import TaskRepo
from jarvis.tools import get_user_context


@tool
async def create_task(
    title: str,
    due_date: str = "",
    due_time: str = "",
    priority: str = "medium",
    category: str = "",
    description: str = "",
    *,
    config: RunnableConfig,
) -> str:
    """Create a new task or reminder. due_date: YYYY-MM-DD, due_time: HH:MM.
    Priority: low, medium, high, urgent. Category: work, personal, health, etc."""
    ctx = get_user_context(config)
    await TaskRepo.create(
        user_id=ctx.user_id,
        title=title,
        description=description or None,
        priority=priority,
        category=category or None,
        due_date=due_date or None,
        due_time=due_time or None,
    )
    parts = [f"Task created: {title}"]
    if priority != "medium":
        parts.append(f"priority: {priority}")
    if due_date:
        parts.append(f"due: {due_date}" + (f" {due_time}" if due_time else ""))
    if category:
        parts.append(f"category: {category}")
    return " | ".join(parts)


@tool
async def list_tasks(status: str = "pending", *, config: RunnableConfig) -> str:
    """List tasks. Status can be 'pending', 'completed', or 'all'."""
    ctx = get_user_context(config)
    rows = await TaskRepo.list_tasks(ctx.user_id, status)
    if not rows:
        return f"No {status} tasks found."
    lines = []
    for row in rows:
        check = "x" if row["status"] == "completed" else " "
        due = f" (due: {row['due_date']}" + (f" {row['due_time']}" if row.get("due_time") else "") + ")" if row.get("due_date") else ""
        pri = f" [{row['priority']}]" if row.get("priority") and row["priority"] != "medium" else ""
        cat = f" #{row['category']}" if row.get("category") else ""
        lines.append(f"[{check}] #{row['id']}: {row['title']}{pri}{due}{cat}")
    return "\n".join(lines)


@tool
async def complete_task(task_id: int, *, config: RunnableConfig) -> str:
    """Mark a task as completed by its ID number."""
    ctx = get_user_context(config)
    success = await TaskRepo.complete(ctx.user_id, task_id)
    if not success:
        return f"Task #{task_id} not found."
    return f"Task #{task_id} marked as completed."


@tool
async def delete_task(task_id: int, *, config: RunnableConfig) -> str:
    """Delete a task by its ID number."""
    ctx = get_user_context(config)
    success = await TaskRepo.delete(ctx.user_id, task_id)
    if not success:
        return f"Task #{task_id} not found."
    return f"Task #{task_id} deleted."
