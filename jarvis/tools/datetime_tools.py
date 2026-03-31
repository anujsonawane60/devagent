from datetime import datetime, timezone

from langchain_core.tools import tool


@tool
def get_current_time(timezone_name: str = "UTC") -> str:
    """Get the current date and time. Optionally specify a timezone like 'Asia/Kolkata', 'US/Eastern', etc."""
    try:
        from zoneinfo import ZoneInfo

        tz = ZoneInfo(timezone_name)
    except (ImportError, KeyError):
        tz = timezone.utc
        timezone_name = "UTC"

    now = datetime.now(tz)
    return f"Current time ({timezone_name}): {now.strftime('%Y-%m-%d %H:%M:%S %Z')}"
