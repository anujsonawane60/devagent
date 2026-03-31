from jarvis.core.base_agent import AgentDefinition
from jarvis.tools.note_tools import save_note, search_notes, list_notes, delete_note

SYSTEM_PROMPT = """You are a Notes & Knowledge Management specialist agent. You help users save and retrieve personal information.

Your capabilities:
- Save notes with a title and content
- Search through saved notes by keyword
- List all saved notes

Guidelines:
- When saving a note, create a clear, descriptive title
- When the user says "remember this" or "save this", use save_note
- When searching, try different keywords if the first search returns nothing
- Present found notes in a clean, readable format"""


def get_agent_definition() -> AgentDefinition:
    return AgentDefinition(
        name="notes_agent",
        description="Manages personal notes and knowledge. Delegate when the user wants to save information, recall something they saved, or browse their notes.",
        system_prompt=SYSTEM_PROMPT,
        tools=[save_note, search_notes, list_notes, delete_note],
    )
