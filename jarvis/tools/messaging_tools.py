from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig

from jarvis.core.credentials import check_credentials
from jarvis.config import settings
from jarvis.tools import get_user_context

_SMS_CREDS = dict(
    TWILIO_ACCOUNT_SID="Twilio Account SID",
    TWILIO_AUTH_TOKEN="Twilio Auth Token",
    TWILIO_PHONE_NUMBER="Twilio phone number",
)

_WA_CREDS = dict(
    TWILIO_ACCOUNT_SID="Twilio Account SID",
    TWILIO_AUTH_TOKEN="Twilio Auth Token",
    TWILIO_WHATSAPP_NUMBER="Twilio WhatsApp number",
)


def _get_twilio_client():
    from twilio.rest import Client
    return Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)


@tool
async def send_sms(to: str, message: str, *, config: RunnableConfig) -> str:
    """Send an SMS message. 'to' must be a phone number with country code (e.g., +919876543210)."""
    msg = check_credentials("Twilio SMS", **_SMS_CREDS)
    if msg:
        return msg

    client = _get_twilio_client()
    result = client.messages.create(
        body=message,
        from_=settings.TWILIO_PHONE_NUMBER,
        to=to,
    )
    return f"SMS sent to {to} (SID: {result.sid})"


@tool
async def send_whatsapp(to: str, message: str, *, config: RunnableConfig) -> str:
    """Send a WhatsApp message via Twilio. 'to' must include country code (e.g., +919876543210)."""
    msg = check_credentials("WhatsApp", **_WA_CREDS)
    if msg:
        return msg

    client = _get_twilio_client()
    # Twilio WhatsApp format
    wa_to = f"whatsapp:{to}" if not to.startswith("whatsapp:") else to
    wa_from = settings.TWILIO_WHATSAPP_NUMBER
    if not wa_from.startswith("whatsapp:"):
        wa_from = f"whatsapp:{wa_from}"

    result = client.messages.create(
        body=message,
        from_=wa_from,
        to=wa_to,
    )
    return f"WhatsApp message sent to {to} (SID: {result.sid})"
