def get_all_tools() -> list:
    """Return all available tools (used for single-agent fallback mode)."""
    from jarvis.tools.task_tools import create_task, list_tasks, complete_task, delete_task
    from jarvis.tools.search_tools import web_search
    from jarvis.tools.datetime_tools import get_current_time
    from jarvis.tools.note_tools import save_note, search_notes, list_notes, delete_note
    from jarvis.tools.contact_tools import save_contact, find_contact, update_contact, list_contacts, delete_contact
    from jarvis.tools.thought_tools import save_thought, search_thoughts, list_thoughts, pin_thought, delete_thought
    from jarvis.tools.vault_tools import store_secret, get_secret, list_secrets, delete_secret
    from jarvis.tools.memory_tools import learn_fact, recall, forget
    from jarvis.tools.scheduler_tools import schedule_action, list_schedules, cancel_schedule

    return [
        create_task, list_tasks, complete_task, delete_task,
        web_search, get_current_time,
        save_note, search_notes, list_notes, delete_note,
        save_contact, find_contact, update_contact, list_contacts, delete_contact,
        save_thought, search_thoughts, list_thoughts, pin_thought, delete_thought,
        store_secret, get_secret, list_secrets, delete_secret,
        learn_fact, recall, forget,
        schedule_action, list_schedules, cancel_schedule,
    ]
