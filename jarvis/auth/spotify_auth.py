"""
Spotify OAuth2 helper.

One-time setup:
    python -m jarvis.auth.spotify_auth

This opens a browser, user logs in, and token is saved.
"""

import json
from pathlib import Path

from jarvis.config import settings


def get_spotify_client():
    """Get an authenticated Spotify client. Returns None if not configured."""
    import spotipy
    from spotipy.oauth2 import SpotifyOAuth

    if not settings.SPOTIFY_CLIENT_ID or not settings.SPOTIFY_CLIENT_SECRET:
        return None

    cache_path = settings.SPOTIFY_TOKEN_PATH
    Path(cache_path).parent.mkdir(parents=True, exist_ok=True)

    sp_oauth = SpotifyOAuth(
        client_id=settings.SPOTIFY_CLIENT_ID,
        client_secret=settings.SPOTIFY_CLIENT_SECRET,
        redirect_uri=settings.SPOTIFY_REDIRECT_URI,
        scope="user-read-playback-state user-modify-playback-state user-read-currently-playing playlist-read-private",
        cache_path=cache_path,
    )

    token_info = sp_oauth.get_cached_token()
    if not token_info:
        return None

    return spotipy.Spotify(auth=token_info["access_token"])


def run_auth_flow():
    """Interactive OAuth flow — run once to authorize Spotify."""
    import spotipy
    from spotipy.oauth2 import SpotifyOAuth

    if not settings.SPOTIFY_CLIENT_ID or not settings.SPOTIFY_CLIENT_SECRET:
        print("ERROR: Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET in .env first.")
        print("Get them from https://developer.spotify.com/dashboard")
        return

    cache_path = settings.SPOTIFY_TOKEN_PATH
    Path(cache_path).parent.mkdir(parents=True, exist_ok=True)

    sp_oauth = SpotifyOAuth(
        client_id=settings.SPOTIFY_CLIENT_ID,
        client_secret=settings.SPOTIFY_CLIENT_SECRET,
        redirect_uri=settings.SPOTIFY_REDIRECT_URI,
        scope="user-read-playback-state user-modify-playback-state user-read-currently-playing playlist-read-private",
        cache_path=cache_path,
    )

    auth_url = sp_oauth.get_authorize_url()
    print(f"Open this URL in your browser:\n{auth_url}\n")

    redirect_url = input("Paste the redirect URL here: ").strip()
    code = sp_oauth.parse_response_code(redirect_url)
    sp_oauth.get_access_token(code)

    print(f"Spotify auth successful! Token saved to: {cache_path}")


if __name__ == "__main__":
    run_auth_flow()
