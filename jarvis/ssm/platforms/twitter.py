from jarvis.ssm.platforms.base import PlatformSpec, register_platform

TWITTER = PlatformSpec(
    name="twitter",
    display_name="Twitter / X",
    max_chars=280,
    max_hashtags=3,
    supports_markdown=False,
    supports_links=True,
    default_tone="casual",
    hashtag_style="inline",
    ideal_length_chars=240,
    emoji_level="minimal",
    style_guide="""Twitter/X best practices:
- Be concise and punchy — every word counts in 280 chars
- Use a strong opinion or hot take to drive engagement
- One idea per tweet — don't try to say everything
- Use 1-2 hashtags max, woven into the text naturally
- Thread format works well for longer content (but generate single tweet here)
- Questions and polls drive replies
- Avoid filler words — cut ruthlessly
- Numbers, stats, and contrarian takes perform well""",
)

register_platform(TWITTER)
