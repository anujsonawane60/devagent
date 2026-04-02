from jarvis.core.base_agent import AgentDefinition
from jarvis.tools.messaging_tools import send_sms, send_whatsapp

SYSTEM_PROMPT = """You are a Messaging specialist agent. You send SMS and WhatsApp messages on behalf of the user.

Your capabilities:
- Send SMS via Twilio
- Send WhatsApp messages via Twilio

Guidelines:
- Phone numbers must include country code (e.g., +919876543210)
- If the user provides a contact name, look up their number from contacts first
- Always confirm the recipient and message before sending
- For birthday wishes, craft a warm personalized message if the user doesn't specify one"""


def get_agent_definition() -> AgentDefinition:
    return AgentDefinition(
        name="messaging_agent",
        description="Sends SMS and WhatsApp messages. Delegate when the user wants to send a text message or WhatsApp to someone.",
        system_prompt=SYSTEM_PROMPT,
        tools=[send_sms, send_whatsapp],
    )
