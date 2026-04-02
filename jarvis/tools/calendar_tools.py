from datetime import datetime, timedelta

from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig

from jarvis.core.credentials import check_credentials
from jarvis.tools import get_user_context

_CRED_CHECK = dict(GOOGLE_CREDENTIALS_PATH="Google OAuth credentials.json path")


def _get_calendar_service():
    from googleapiclient.discovery import build
    from jarvis.auth.google_auth import get_google_credentials

    creds = get_google_credentials()
    if not creds:
        return None
    return build("calendar", "v3", credentials=creds)


@tool
async def list_events(days: int = 1, *, config: RunnableConfig) -> str:
    """List upcoming calendar events for the next N days (default: today)."""
    msg = check_credentials("Google Calendar", **_CRED_CHECK)
    if msg:
        return msg

    service = _get_calendar_service()
    if not service:
        return "Google Calendar token expired. Please run: python -m jarvis.auth.google_auth"

    now = datetime.utcnow()
    time_min = now.isoformat() + "Z"
    time_max = (now + timedelta(days=days)).isoformat() + "Z"

    results = service.events().list(
        calendarId="primary", timeMin=time_min, timeMax=time_max,
        maxResults=20, singleEvents=True, orderBy="startTime"
    ).execute()

    events = results.get("items", [])
    if not events:
        return f"No events in the next {days} day(s)."

    lines = []
    for e in events:
        start = e["start"].get("dateTime", e["start"].get("date", ""))
        summary = e.get("summary", "(no title)")
        location = e.get("location", "")
        line = f"- **{summary}** at {start}"
        if location:
            line += f" ({location})"
        lines.append(line)

    return "\n".join(lines)


@tool
async def create_event(
    summary: str,
    start_time: str,
    end_time: str = "",
    description: str = "",
    location: str = "",
    *,
    config: RunnableConfig,
) -> str:
    """Create a Google Calendar event. start_time/end_time format: YYYY-MM-DDTHH:MM:SS.
    If end_time not provided, defaults to 1 hour after start."""
    msg = check_credentials("Google Calendar", **_CRED_CHECK)
    if msg:
        return msg

    service = _get_calendar_service()
    if not service:
        return "Google Calendar token expired. Please run: python -m jarvis.auth.google_auth"

    if not end_time:
        start_dt = datetime.fromisoformat(start_time)
        end_time = (start_dt + timedelta(hours=1)).isoformat()

    event = {
        "summary": summary,
        "start": {"dateTime": start_time, "timeZone": "UTC"},
        "end": {"dateTime": end_time, "timeZone": "UTC"},
    }
    if description:
        event["description"] = description
    if location:
        event["location"] = location

    created = service.events().insert(calendarId="primary", body=event).execute()
    return f"Event created: {summary} at {start_time}" + (f" ({location})" if location else "")


@tool
async def check_availability(date: str, *, config: RunnableConfig) -> str:
    """Check if the user is free on a given date (YYYY-MM-DD). Shows busy/free slots."""
    msg = check_credentials("Google Calendar", **_CRED_CHECK)
    if msg:
        return msg

    service = _get_calendar_service()
    if not service:
        return "Google Calendar token expired. Please run: python -m jarvis.auth.google_auth"

    time_min = f"{date}T00:00:00Z"
    time_max = f"{date}T23:59:59Z"

    results = service.events().list(
        calendarId="primary", timeMin=time_min, timeMax=time_max,
        singleEvents=True, orderBy="startTime"
    ).execute()

    events = results.get("items", [])
    if not events:
        return f"You're completely free on {date}!"

    lines = [f"Events on {date}:"]
    for e in events:
        start = e["start"].get("dateTime", e["start"].get("date", ""))
        end = e["end"].get("dateTime", e["end"].get("date", ""))
        summary = e.get("summary", "(no title)")
        lines.append(f"- {summary}: {start} to {end}")

    return "\n".join(lines)
