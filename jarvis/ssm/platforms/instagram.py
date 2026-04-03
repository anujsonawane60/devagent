from jarvis.ssm.platforms.base import PlatformSpec, register_platform

INSTAGRAM = PlatformSpec(
    name="instagram",
    display_name="Instagram",
    max_chars=2200,
    max_hashtags=20,
    supports_markdown=False,
    supports_links=False,
    default_tone="casual",
    hashtag_style="block",
    ideal_length_chars=800,
    emoji_level="heavy",
    style_guide="""Instagram caption best practices:
- Start with an attention-grabbing first line (shown before "more")
- Use a conversational, relatable tone
- Tell a micro-story or share a personal moment
- Use emojis generously to add personality and break up text
- Include a clear call-to-action ("Double tap if you agree", "Save this for later")
- Add 15-20 relevant hashtags in a separate block at the end
- Mix popular and niche hashtags for reach + targeting
- Use line breaks liberally — walls of text don't work
- Suggest an image/visual concept since Instagram is visual-first
- Links don't work in captions — say "link in bio" if needed""",
)

register_platform(INSTAGRAM)
