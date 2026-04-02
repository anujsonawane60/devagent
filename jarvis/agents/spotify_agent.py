from jarvis.core.base_agent import AgentDefinition
from jarvis.tools.spotify_tools import now_playing, search_music, play_track, pause_music, skip_track

SYSTEM_PROMPT = """You are a Spotify specialist agent. You control the user's Spotify playback.

Your capabilities:
- Show what's currently playing
- Search for tracks
- Play a track by name
- Pause playback
- Skip to next track

Guidelines:
- Playback control (play, pause, skip) requires Spotify Premium and an active device
- If no device is active, suggest the user opens Spotify first
- When searching, present results with artist names
- Keep responses musical and fun"""


def get_agent_definition() -> AgentDefinition:
    return AgentDefinition(
        name="spotify_agent",
        description="Controls Spotify — play music, search tracks, see what's playing, pause, skip. Delegate when the user asks about music or wants to control playback.",
        system_prompt=SYSTEM_PROMPT,
        tools=[now_playing, search_music, play_track, pause_music, skip_track],
    )
