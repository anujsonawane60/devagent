import base64
from email.mime.text import MIMEText

from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig

from jarvis.core.credentials import check_credentials
from jarvis.tools import get_user_context

_CRED_CHECK = dict(GOOGLE_CREDENTIALS_PATH="Google OAuth credentials.json path")


def _get_gmail_service():
    from googleapiclient.discovery import build
    from jarvis.auth.google_auth import get_google_credentials

    creds = get_google_credentials()
    if not creds:
        return None
    return build("gmail", "v1", credentials=creds)


@tool
async def read_inbox(max_results: int = 5, *, config: RunnableConfig) -> str:
    """Read recent emails from Gmail inbox."""
    msg = check_credentials("Gmail", **_CRED_CHECK)
    if msg:
        return msg

    service = _get_gmail_service()
    if not service:
        return "Gmail token expired. Please run: python -m jarvis.auth.google_auth"

    results = service.users().messages().list(
        userId="me", labelIds=["INBOX"], maxResults=max_results
    ).execute()

    messages = results.get("messages", [])
    if not messages:
        return "Your inbox is empty."

    lines = []
    for m in messages:
        msg_data = service.users().messages().get(userId="me", id=m["id"], format="metadata").execute()
        headers = {h["name"]: h["value"] for h in msg_data.get("payload", {}).get("headers", [])}
        subject = headers.get("Subject", "(no subject)")
        sender = headers.get("From", "unknown")
        snippet = msg_data.get("snippet", "")[:100]
        lines.append(f"- **{subject}**\n  From: {sender}\n  {snippet}")

    return "\n\n".join(lines)


@tool
async def send_email(to: str, subject: str, body: str, *, config: RunnableConfig) -> str:
    """Send an email via Gmail. 'to' is the recipient email address."""
    msg = check_credentials("Gmail", **_CRED_CHECK)
    if msg:
        return msg

    service = _get_gmail_service()
    if not service:
        return "Gmail token expired. Please run: python -m jarvis.auth.google_auth"

    message = MIMEText(body)
    message["to"] = to
    message["subject"] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

    service.users().messages().send(userId="me", body={"raw": raw}).execute()
    return f"Email sent to {to}: {subject}"


@tool
async def search_email(query: str, max_results: int = 5, *, config: RunnableConfig) -> str:
    """Search Gmail with a query (e.g., 'from:raj@gmail.com', 'subject:meeting', 'is:unread')."""
    msg = check_credentials("Gmail", **_CRED_CHECK)
    if msg:
        return msg

    service = _get_gmail_service()
    if not service:
        return "Gmail token expired. Please run: python -m jarvis.auth.google_auth"

    results = service.users().messages().list(
        userId="me", q=query, maxResults=max_results
    ).execute()

    messages = results.get("messages", [])
    if not messages:
        return f"No emails found for: {query}"

    lines = []
    for m in messages:
        msg_data = service.users().messages().get(userId="me", id=m["id"], format="metadata").execute()
        headers = {h["name"]: h["value"] for h in msg_data.get("payload", {}).get("headers", [])}
        subject = headers.get("Subject", "(no subject)")
        sender = headers.get("From", "unknown")
        lines.append(f"- **{subject}** from {sender}")

    return "\n".join(lines)
