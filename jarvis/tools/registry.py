def get_all_tools() -> list:
    """Return all available tools for the agent system."""
    from jarvis.tools.task_tools import create_task, list_tasks, complete_task
    from jarvis.tools.search_tools import web_search
    from jarvis.tools.datetime_tools import get_current_time
    from jarvis.tools.note_tools import save_note, search_notes, list_notes

    return [
        create_task,
        list_tasks,
        complete_task,
        web_search,
        get_current_time,
        save_note,
        search_notes,
        list_notes,
    ]
