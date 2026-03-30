from langchain_core.tools import tool as langchain_tool

# Re-export the langchain tool decorator for convenience
tool = langchain_tool


def get_all_tools() -> list:
    from jarvis.tools.task_manager import create_task, list_tasks, complete_task
    from jarvis.tools.web_search import web_search
    from jarvis.tools.datetime_tool import get_current_time
    from jarvis.tools.notes import save_note, search_notes, list_notes

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
