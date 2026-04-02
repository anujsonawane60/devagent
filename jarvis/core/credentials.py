"""
Credential checker — gracefully handles missing API keys/tokens.

Tools call check_credentials() before doing anything. If credentials
are missing, it returns a user-friendly message that the agent passes
back. The user only sees this when they TRY to use the feature.

Usage in tools:
    from jarvis.core.credentials import check_credentials

    @tool
    async def read_inbox(...) -> str:
        msg = check_credentials("Gmail", GOOGLE_CREDENTIALS_PATH="path/to/credentials.json")
        if msg:
            return msg  # "Gmail is not configured. ..."
        # ... actual logic
"""

from jarvis.config import settings


# Friendly setup instructions per service
SETUP_INSTRUCTIONS = {
    "Gmail": (
        "To set up Gmail:\n"
        "1. Create a Google Cloud Project at https://console.cloud.google.com\n"
        "2. Enable Gmail API\n"
        "3. Create OAuth2 credentials (Desktop app)\n"
        "4. Download credentials.json\n"
        "5. Set GOOGLE_CREDENTIALS_PATH in .env\n"
        "6. Run: python -m jarvis.auth.google_auth"
    ),
    "Google Calendar": (
        "To set up Google Calendar:\n"
        "1. Create a Google Cloud Project at https://console.cloud.google.com\n"
        "2. Enable Google Calendar API\n"
        "3. Create OAuth2 credentials (Desktop app)\n"
        "4. Download credentials.json\n"
        "5. Set GOOGLE_CREDENTIALS_PATH in .env\n"
        "6. Run: python -m jarvis.auth.google_auth"
    ),
    "GitHub": (
        "To set up GitHub:\n"
        "1. Go to https://github.com/settings/tokens\n"
        "2. Generate a personal access token (classic)\n"
        "3. Set GITHUB_TOKEN in .env"
    ),
    "Twilio SMS": (
        "To set up SMS:\n"
        "1. Sign up at https://www.twilio.com\n"
        "2. Get Account SID, Auth Token, and a phone number\n"
        "3. Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER in .env"
    ),
    "WhatsApp": (
        "To set up WhatsApp:\n"
        "1. Sign up at https://www.twilio.com\n"
        "2. Enable WhatsApp sandbox in Twilio console\n"
        "3. Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER in .env"
    ),
    "Notion": (
        "To set up Notion:\n"
        "1. Go to https://www.notion.so/my-integrations\n"
        "2. Create a new integration\n"
        "3. Copy the Internal Integration Token\n"
        "4. Set NOTION_TOKEN in .env\n"
        "5. Share your Notion pages/databases with the integration"
    ),
    "Spotify": (
        "To set up Spotify:\n"
        "1. Go to https://developer.spotify.com/dashboard\n"
        "2. Create a new app (redirect URI: http://localhost:8888/callback)\n"
        "3. Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET in .env\n"
        "4. Run: python -m jarvis.auth.spotify_auth"
    ),
}


def check_credentials(service_name: str, **required_settings) -> str | None:
    """
    Check if required credentials are set in config.

    Args:
        service_name: Display name ("Gmail", "GitHub", etc.)
        **required_settings: setting_name=description pairs
            e.g., GITHUB_TOKEN="GitHub personal access token"

    Returns:
        None if all credentials are present (good to go).
        A friendly error message string if something is missing.
    """
    missing = []
    for setting_name, description in required_settings.items():
        value = getattr(settings, setting_name, "")
        if not value:
            missing.append(f"  - {setting_name} ({description})")

    if not missing:
        return None

    # Build user-friendly message
    msg = f"{service_name} is not configured yet.\n\nMissing:\n"
    msg += "\n".join(missing)

    instructions = SETUP_INSTRUCTIONS.get(service_name)
    if instructions:
        msg += f"\n\n{instructions}"

    return msg
