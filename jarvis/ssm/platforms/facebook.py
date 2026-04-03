from jarvis.ssm.platforms.base import PlatformSpec, register_platform

FACEBOOK = PlatformSpec(
    name="facebook",
    display_name="Facebook",
    max_chars=63206,
    max_hashtags=5,
    supports_markdown=False,
    supports_links=True,
    default_tone="casual",
    hashtag_style="inline",
    ideal_length_chars=500,
    emoji_level="moderate",
    style_guide="""Facebook post best practices:
- Keep it concise — shorter posts get more engagement (40-80 chars is optimal)
- But for thought leadership, 500-1000 chars performs well too
- Use a conversational, friendly tone — Facebook is personal
- Ask questions to drive comments
- Use 1-3 hashtags max — Facebook isn't hashtag-heavy
- Include a link if sharing an article (Facebook shows rich previews)
- Emojis are welcome but don't overdo it
- Tag people/pages when relevant
- "Share-worthy" content performs best — think: would someone share this?""",
)

register_platform(FACEBOOK)
