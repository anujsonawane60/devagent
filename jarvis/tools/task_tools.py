from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig

from jarvis.db.repositories import TaskRepo
from jarvis.tools import get_user_context


@tool
async def create_task(title: str, due_date: str = "", *, config: RunnableConfig) -> str:
    """Create a new task or reminder. Use due_date in YYYY-MM-DD format if the user specifies a deadline."""
    ctx = get_user_context(config)
    await TaskRepo.create(ctx.user_id, title, due_date or None)
    due = f" (due: {due_date})" if due_date else ""
    return f"Task created: {title}{due}"


@tool
async def list_tasks(status: str = "pending", *, config: RunnableConfig) -> str:
    """List tasks. Status can be 'pending', 'completed', or 'all'."""
    ctx = get_user_context(config)
    rows = await TaskRepo.list_tasks(ctx.user_id, status)
    if not rows:
        return f"No {status} tasks found."
    lines = []
    for row in rows:
        due = f" (due: {row['due_date']})" if row["due_date"] else ""
        check = "x" if row["status"] == "completed" else " "
        lines.append(f"[{check}] #{row['id']}: {row['title']}{due}")
    return "\n".join(lines)


@tool
async def complete_task(task_id: int, *, config: RunnableConfig) -> str:
    """Mark a task as completed by its ID number."""
    ctx = get_user_context(config)
    success = await TaskRepo.complete(ctx.user_id, task_id)
    if not success:
        return f"Task #{task_id} not found."
    return f"Task #{task_id} marked as completed."
