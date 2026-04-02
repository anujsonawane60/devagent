"""
Google OAuth2 helper for Gmail + Calendar.

One-time setup:
    python -m jarvis.auth.google_auth

This opens a browser, user logs in, and token.json is saved.
After that, tools use the token automatically.
"""

import json
import logging
from pathlib import Path

from jarvis.config import settings

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/calendar.events",
]


def get_google_credentials():
    """Get valid Google credentials, refreshing if needed. Returns None if not configured."""
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request

    token_path = settings.GOOGLE_TOKEN_PATH
    creds_path = settings.GOOGLE_CREDENTIALS_PATH

    if not creds_path:
        return None

    creds = None

    # Load existing token
    if Path(token_path).exists():
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    # Refresh if expired
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            _save_token(creds, token_path)
        except Exception:
            creds = None

    if not creds or not creds.valid:
        return None

    return creds


def _save_token(creds, token_path: str):
    """Save credentials to token file."""
    Path(token_path).parent.mkdir(parents=True, exist_ok=True)
    with open(token_path, "w") as f:
        f.write(creds.to_json())


def run_auth_flow():
    """Interactive OAuth flow — run once to generate token.json."""
    from google_auth_oauthlib.flow import InstalledAppFlow

    creds_path = settings.GOOGLE_CREDENTIALS_PATH
    token_path = settings.GOOGLE_TOKEN_PATH

    if not creds_path or not Path(creds_path).exists():
        print(f"ERROR: credentials.json not found at: {creds_path}")
        print("Download it from Google Cloud Console > APIs > Credentials")
        return

    flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
    creds = flow.run_local_server(port=0)

    _save_token(creds, token_path)
    print(f"Google auth successful! Token saved to: {token_path}")
    print("Gmail and Google Calendar are now ready to use.")


if __name__ == "__main__":
    run_auth_flow()
