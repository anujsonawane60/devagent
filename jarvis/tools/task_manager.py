from langchain_core.tools import tool
from jarvis.db.database import get_db


@tool
async def create_task(title: str, due_date: str = "") -> str:
    """Create a new task or reminder. Use due_date in YYYY-MM-DD format if the user specifies a deadline."""
    db = await get_db()
    try:
        await db.execute(
            "INSERT INTO tasks (chat_id, title, due_date) VALUES ('global', ?, ?)",
            (title, due_date or None),
        )
        await db.commit()
        due = f" (due: {due_date})" if due_date else ""
        return f"Task created: {title}{due}"
    finally:
        await db.close()


@tool
async def list_tasks(status: str = "pending") -> str:
    """List tasks. Status can be 'pending', 'completed', or 'all'."""
    db = await get_db()
    try:
        if status == "all":
            cursor = await db.execute(
                "SELECT id, title, due_date, status FROM tasks WHERE chat_id = 'global' ORDER BY created_at DESC"
            )
        else:
            cursor = await db.execute(
                "SELECT id, title, due_date, status FROM tasks WHERE chat_id = 'global' AND status = ? ORDER BY created_at DESC",
                (status,),
            )
        rows = await cursor.fetchall()
        if not rows:
            return f"No {status} tasks found."
        lines = []
        for row in rows:
            due = f" (due: {row[2]})" if row[2] else ""
            check = "x" if row[3] == "completed" else " "
            lines.append(f"[{check}] #{row[0]}: {row[1]}{due}")
        return "\n".join(lines)
    finally:
        await db.close()


@tool
async def complete_task(task_id: int) -> str:
    """Mark a task as completed by its ID number."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "UPDATE tasks SET status = 'completed', completed_at = CURRENT_TIMESTAMP WHERE id = ? AND chat_id = 'global'",
            (task_id,),
        )
        await db.commit()
        if cursor.rowcount == 0:
            return f"Task #{task_id} not found."
        return f"Task #{task_id} marked as completed."
    finally:
        await db.close()
