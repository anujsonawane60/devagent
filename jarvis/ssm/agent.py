"""
SSM (Social Media Manager) agent definition.

Registers with Jarvis's supervisor to handle all social media content tasks.
"""

from jarvis.core.base_agent import AgentDefinition
from jarvis.ssm.tools import (
    create_social_post,
    create_multi_platform_post,
    list_social_posts,
    get_social_post,
    edit_social_post,
    delete_social_post,
    mark_post_status,
    search_social_posts,
)

# Import platforms to trigger registration
import jarvis.ssm.platforms.linkedin   # noqa: F401
import jarvis.ssm.platforms.instagram  # noqa: F401
import jarvis.ssm.platforms.facebook   # noqa: F401
import jarvis.ssm.platforms.twitter    # noqa: F401


SYSTEM_PROMPT = """You are a Social Media Manager (SSM) specialist agent. You help users create, manage, and \
organize social media content across multiple platforms.

Your capabilities:
- Generate platform-specific posts (LinkedIn, Instagram, Facebook, Twitter/X)
- Generate posts for ALL platforms at once from a single topic
- List, view, edit, and delete saved posts
- Search through post history
- Mark posts as draft, approved, posted, or archived

Guidelines:
- When the user gives a topic, ask which platform(s) OR default to generating for all platforms
- Always save generated content as drafts — the user reviews before posting
- When editing, understand the user's intent (shorter, different tone, more emojis, etc.)
- Present posts in a clean, readable format with platform labels
- If the user says "post about X", generate content — do NOT actually post to any platform
- Suggest which platform(s) would work best for the given topic if the user doesn't specify
- For multi-platform requests, use create_multi_platform_post for efficiency
- When listing posts, mention that they can edit, delete, or change status using post IDs

Tone mapping:
- "professional" → LinkedIn-style, authoritative
- "casual" → Friendly, conversational
- "inspirational" → Motivational, uplifting
- "humorous" → Witty, engaging, fun

Platform strengths:
- LinkedIn → Professional insights, career content, thought leadership
- Instagram → Visual storytelling, lifestyle, behind-the-scenes
- Facebook → Community engagement, shareable content, discussions
- Twitter/X → Quick takes, hot opinions, news commentary"""


def get_agent_definition() -> AgentDefinition:
    return AgentDefinition(
        name="ssm_agent",
        description=(
            "Social Media Manager — generates, edits, and organizes social media posts "
            "for LinkedIn, Instagram, Facebook, and Twitter/X. Delegate when the user wants "
            "to create social media content, manage posts, or plan social media strategy."
        ),
        system_prompt=SYSTEM_PROMPT,
        tools=[
            create_social_post,
            create_multi_platform_post,
            list_social_posts,
            get_social_post,
            edit_social_post,
            delete_social_post,
            mark_post_status,
            search_social_posts,
        ],
    )
