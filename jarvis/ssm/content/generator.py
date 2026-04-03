"""
LLM-powered content generator for social media posts.

Takes a topic + platform + tone and produces platform-optimized content
using the platform's style guide and constraints.
"""

import logging
from langchain_core.messages import SystemMessage, HumanMessage

from jarvis.core.llm_factory import create_llm
from jarvis.ssm.platforms.base import get_platform, get_all_platforms, PlatformSpec

logger = logging.getLogger(__name__)


GENERATOR_SYSTEM_PROMPT = """You are an expert social media content creator. You generate high-quality, \
engaging posts tailored to specific platforms.

RULES:
- Follow the platform's style guide EXACTLY
- Stay within the character limit
- Generate ONLY the post content — no explanations, no "Here's your post:", no meta-commentary
- Include hashtags as specified by the platform style
- Match the requested tone precisely
- If a target audience is specified, tailor language and references to them
- Make the content feel authentic and human, not AI-generated
- Every post must have a clear hook in the first line"""


GENERATION_PROMPT = """Generate a {platform_name} post about the following topic:

TOPIC: {topic}

PLATFORM: {platform_name}
CHARACTER LIMIT: {max_chars}
TONE: {tone}
{audience_line}

PLATFORM STYLE GUIDE:
{style_guide}

IMPORTANT:
- Output ONLY the post text (including hashtags if applicable)
- Do NOT include any prefix like "Here's your post:" or explanations
- Stay under {max_chars} characters
- Use {emoji_level} emoji usage"""


MULTI_PLATFORM_PROMPT = """Generate social media posts about the following topic for ALL platforms listed below.

TOPIC: {topic}
TONE: {tone}
{audience_line}

For EACH platform, generate a separate post following that platform's rules.
Output format — use exactly this format with the separator:

---PLATFORM: LinkedIn---
(linkedin post here)

---PLATFORM: Instagram---
(instagram post here)

---PLATFORM: Facebook---
(facebook post here)

---PLATFORM: Twitter / X---
(twitter post here)

PLATFORM GUIDES:
{all_guides}

IMPORTANT:
- Output ONLY the posts in the format above
- No additional commentary or explanations
- Each post must follow its platform's character limit and style"""


EDIT_PROMPT = """Edit the following social media post based on the user's instructions.

CURRENT POST ({platform_name}):
{current_content}

USER'S EDIT REQUEST: {edit_instruction}

PLATFORM RULES:
- Character limit: {max_chars}
- Style: {style_guide}

Output ONLY the edited post text. No explanations."""


async def generate_post(
    topic: str,
    platform_name: str,
    tone: str = "professional",
    target_audience: str | None = None,
) -> dict:
    """
    Generate a single post for one platform.

    Returns: {"content": str, "hashtags": str, "media_suggestion": str, "platform": str}
    """
    spec = get_platform(platform_name)
    if not spec:
        return {"error": f"Unknown platform: {platform_name}. Supported: linkedin, instagram, facebook, twitter"}

    audience_line = f"TARGET AUDIENCE: {target_audience}" if target_audience else ""

    prompt = GENERATION_PROMPT.format(
        platform_name=spec.display_name,
        topic=topic,
        max_chars=spec.max_chars,
        tone=tone,
        audience_line=audience_line,
        style_guide=spec.style_guide,
        emoji_level=spec.emoji_level,
    )

    llm = create_llm(temperature=0.8)
    response = await llm.ainvoke([
        SystemMessage(content=GENERATOR_SYSTEM_PROMPT),
        HumanMessage(content=prompt),
    ])

    content = response.content.strip()

    # Extract hashtags if present
    hashtags = _extract_hashtags(content)

    # Generate media suggestion for visual platforms
    media_suggestion = None
    if platform_name in ("instagram", "facebook"):
        media_suggestion = await _suggest_media(topic, platform_name)

    return {
        "platform": platform_name,
        "content": content,
        "hashtags": hashtags,
        "media_suggestion": media_suggestion,
    }


async def generate_multi_platform(
    topic: str,
    tone: str = "professional",
    target_audience: str | None = None,
    platforms: list[str] | None = None,
) -> list[dict]:
    """
    Generate posts for multiple platforms at once.

    Returns: list of {"platform": str, "content": str, "hashtags": str}
    """
    if platforms:
        specs = [get_platform(p) for p in platforms]
        specs = [s for s in specs if s is not None]
    else:
        specs = get_all_platforms()

    if not specs:
        return [{"error": "No valid platforms specified."}]

    audience_line = f"TARGET AUDIENCE: {target_audience}" if target_audience else ""

    all_guides = "\n\n".join(
        f"=== {s.display_name} (max {s.max_chars} chars, {s.emoji_level} emojis) ===\n{s.style_guide}"
        for s in specs
    )

    prompt = MULTI_PLATFORM_PROMPT.format(
        topic=topic,
        tone=tone,
        audience_line=audience_line,
        all_guides=all_guides,
    )

    llm = create_llm(temperature=0.8)
    response = await llm.ainvoke([
        SystemMessage(content=GENERATOR_SYSTEM_PROMPT),
        HumanMessage(content=prompt),
    ])

    return _parse_multi_platform_response(response.content, specs)


async def edit_post(
    current_content: str,
    edit_instruction: str,
    platform_name: str,
) -> str:
    """Edit an existing post based on user instructions. Returns edited content."""
    spec = get_platform(platform_name)
    if not spec:
        return current_content

    prompt = EDIT_PROMPT.format(
        platform_name=spec.display_name,
        current_content=current_content,
        edit_instruction=edit_instruction,
        max_chars=spec.max_chars,
        style_guide=spec.style_guide,
    )

    llm = create_llm(temperature=0.7)
    response = await llm.ainvoke([
        SystemMessage(content=GENERATOR_SYSTEM_PROMPT),
        HumanMessage(content=prompt),
    ])

    return response.content.strip()


async def _suggest_media(topic: str, platform: str) -> str:
    """Generate a brief image/visual suggestion for the post."""
    llm = create_llm(temperature=0.7)
    response = await llm.ainvoke([
        SystemMessage(content="You suggest visual content ideas for social media posts. Be brief and specific."),
        HumanMessage(content=f"Suggest a single image/visual idea for a {platform} post about: {topic}\n\n"
                             "Reply in one sentence. Example: 'A flat-lay photo of a laptop with code on screen, "
                             "coffee cup, and sticky notes with AI keywords.'"),
    ])
    return response.content.strip()


def _extract_hashtags(content: str) -> str:
    """Pull hashtags out of generated content."""
    tags = [word for word in content.split() if word.startswith("#")]
    return ",".join(tags) if tags else ""


def _parse_multi_platform_response(text: str, specs: list[PlatformSpec]) -> list[dict]:
    """Parse the multi-platform LLM response into separate post dicts."""
    results = []
    # Split by platform separator
    sections = text.split("---PLATFORM:")

    for section in sections:
        section = section.strip()
        if not section:
            continue

        # Extract platform name from "LinkedIn---\n<content>"
        if "---" in section:
            header, content = section.split("---", 1)
            content = content.strip()
        else:
            continue

        # Match to our platform specs
        header_lower = header.strip().lower()
        matched_spec = None
        for spec in specs:
            if spec.display_name.lower() in header_lower or spec.name in header_lower:
                matched_spec = spec
                break

        if matched_spec and content:
            results.append({
                "platform": matched_spec.name,
                "content": content,
                "hashtags": _extract_hashtags(content),
                "media_suggestion": None,
            })

    return results
