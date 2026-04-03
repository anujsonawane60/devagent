from jarvis.ssm.platforms.base import PlatformSpec, register_platform

LINKEDIN = PlatformSpec(
    name="linkedin",
    display_name="LinkedIn",
    max_chars=3000,
    max_hashtags=5,
    supports_markdown=False,
    supports_links=True,
    default_tone="professional",
    hashtag_style="block",
    ideal_length_chars=1200,
    emoji_level="minimal",
    style_guide="""LinkedIn best practices:
- Open with a strong hook (first 2 lines are visible before "see more")
- Use short paragraphs (1-2 sentences) with line breaks between them
- Include a personal angle or insight — not just information
- End with a question or call-to-action to drive engagement
- Use 3-5 relevant hashtags at the end (on a separate line)
- Avoid excessive emojis — keep it professional but human
- Numbers and data points perform well
- Use "I" perspective for personal brand posts
- Do NOT use markdown formatting (no **, no ##, no bullet points with -)
- Use Unicode bullets (•) or line breaks for lists""",
)

register_platform(LINKEDIN)
