"""
Base platform specification. Each platform defines its constraints and formatting rules.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class PlatformSpec:
    """Constraints and style rules for a social media platform."""

    name: str                           # "linkedin", "instagram", "facebook"
    display_name: str                   # "LinkedIn", "Instagram", "Facebook"
    max_chars: int                      # character limit for post text
    max_hashtags: int                   # recommended max hashtags
    supports_markdown: bool = False     # can the platform render markdown?
    supports_links: bool = True         # can we include clickable links?
    default_tone: str = "professional"
    hashtag_style: str = "inline"       # "inline" (in text) or "block" (grouped at end)

    # Platform-specific prompt guidance for the LLM
    style_guide: str = ""

    # Optimal content characteristics
    ideal_length_chars: int = 0         # sweet spot for engagement (0 = use max)
    emoji_level: str = "moderate"       # "none", "minimal", "moderate", "heavy"


# Registry of all supported platforms
_PLATFORMS: dict[str, PlatformSpec] = {}


def register_platform(spec: PlatformSpec):
    _PLATFORMS[spec.name] = spec


def get_platform(name: str) -> PlatformSpec | None:
    return _PLATFORMS.get(name.lower())


def get_all_platforms() -> list[PlatformSpec]:
    return list(_PLATFORMS.values())


def get_platform_names() -> list[str]:
    return list(_PLATFORMS.keys())
