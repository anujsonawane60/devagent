from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig

from jarvis.core.credentials import check_credentials

_CRED_CHECK = dict(
    SPOTIFY_CLIENT_ID="Spotify app client ID",
    SPOTIFY_CLIENT_SECRET="Spotify app client secret",
)


def _get_spotify():
    from jarvis.auth.spotify_auth import get_spotify_client
    return get_spotify_client()


@tool
async def now_playing(*, config: RunnableConfig) -> str:
    """Show what's currently playing on Spotify."""
    msg = check_credentials("Spotify", **_CRED_CHECK)
    if msg:
        return msg

    sp = _get_spotify()
    if not sp:
        return "Spotify token expired. Please run: python -m jarvis.auth.spotify_auth"

    current = sp.current_playback()
    if not current or not current.get("item"):
        return "Nothing is playing right now."

    track = current["item"]
    name = track["name"]
    artists = ", ".join(a["name"] for a in track["artists"])
    album = track["album"]["name"]
    is_playing = "Playing" if current["is_playing"] else "Paused"

    return f"{is_playing}: **{name}** by {artists}\nAlbum: {album}"


@tool
async def search_music(query: str, limit: int = 5, *, config: RunnableConfig) -> str:
    """Search for tracks on Spotify."""
    msg = check_credentials("Spotify", **_CRED_CHECK)
    if msg:
        return msg

    sp = _get_spotify()
    if not sp:
        return "Spotify token expired. Please run: python -m jarvis.auth.spotify_auth"

    results = sp.search(q=query, type="track", limit=limit)
    tracks = results.get("tracks", {}).get("items", [])
    if not tracks:
        return f"No tracks found for: {query}"

    lines = []
    for i, t in enumerate(tracks, 1):
        artists = ", ".join(a["name"] for a in t["artists"])
        lines.append(f"{i}. **{t['name']}** by {artists}")

    return "\n".join(lines)


@tool
async def play_track(query: str = "", *, config: RunnableConfig) -> str:
    """Resume playback or play a specific track. If query is provided, searches and plays it."""
    msg = check_credentials("Spotify", **_CRED_CHECK)
    if msg:
        return msg

    sp = _get_spotify()
    if not sp:
        return "Spotify token expired. Please run: python -m jarvis.auth.spotify_auth"

    try:
        if query:
            results = sp.search(q=query, type="track", limit=1)
            tracks = results.get("tracks", {}).get("items", [])
            if not tracks:
                return f"No tracks found for: {query}"
            track = tracks[0]
            sp.start_playback(uris=[track["uri"]])
            artists = ", ".join(a["name"] for a in track["artists"])
            return f"Now playing: **{track['name']}** by {artists}"
        else:
            sp.start_playback()
            return "Playback resumed."
    except Exception as e:
        if "NO_ACTIVE_DEVICE" in str(e).upper() or "PREMIUM" in str(e).upper():
            return "No active Spotify device found. Open Spotify on a device first. (Playback control requires Spotify Premium)"
        return f"Playback failed: {e}"


@tool
async def pause_music(*, config: RunnableConfig) -> str:
    """Pause Spotify playback."""
    msg = check_credentials("Spotify", **_CRED_CHECK)
    if msg:
        return msg

    sp = _get_spotify()
    if not sp:
        return "Spotify token expired. Please run: python -m jarvis.auth.spotify_auth"

    try:
        sp.pause_playback()
        return "Playback paused."
    except Exception as e:
        return f"Pause failed: {e}"


@tool
async def skip_track(*, config: RunnableConfig) -> str:
    """Skip to the next track on Spotify."""
    msg = check_credentials("Spotify", **_CRED_CHECK)
    if msg:
        return msg

    sp = _get_spotify()
    if not sp:
        return "Spotify token expired. Please run: python -m jarvis.auth.spotify_auth"

    try:
        sp.next_track()
        return "Skipped to next track."
    except Exception as e:
        return f"Skip failed: {e}"
