from jarvis.core.base_agent import AgentDefinition
from jarvis.tools.gmail_tools import read_inbox, send_email, search_email

SYSTEM_PROMPT = """You are an Email specialist agent. You manage the user's Gmail.

Your capabilities:
- Read recent inbox emails
- Send emails
- Search emails with Gmail queries

Guidelines:
- Summarize emails concisely — subject, sender, key point
- Before sending, confirm the recipient and content with the user
- Use Gmail search syntax: from:, to:, subject:, is:unread, has:attachment
- Never expose email content to other agents"""


def get_agent_definition() -> AgentDefinition:
    return AgentDefinition(
        name="email_agent",
        description="Manages Gmail — read inbox, send emails, search mail. Delegate when the user asks about email, wants to send a message via email, or check their inbox.",
        system_prompt=SYSTEM_PROMPT,
        tools=[read_inbox, send_email, search_email],
    )
