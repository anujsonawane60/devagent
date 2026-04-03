"""
LangChain tools for the SSM (Social Media Manager) agent.

These tools are used by the supervisor to delegate social media tasks.
All post CRUD goes through SocialPostRepo, content generation through the generator.
"""

from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig

from jarvis.tools import get_user_context
from jarvis.db.repositories import SocialPostRepo
from jarvis.ssm.content.generator import generate_post, generate_multi_platform, edit_post
from jarvis.ssm.platforms.base import get_platform_names


@tool
async def create_social_post(
    topic: str,
    platform: str,
    tone: str = "professional",
    target_audience: str = "",
    *,
    config: RunnableConfig,
) -> str:
    """Generate a social media post for a specific platform.

    Args:
        topic: What the post should be about (e.g., "AI agents in 2026", "our new product launch")
        platform: Target platform — one of: linkedin, instagram, facebook, twitter
        tone: Writing tone — professional, casual, inspirational, or humorous
        target_audience: Who the post is for (e.g., "developers", "startup founders", "general")
    """
    ctx = get_user_context(config)

    valid_platforms = get_platform_names()
    if platform.lower() not in valid_platforms:
        return f"Unknown platform '{platform}'. Supported: {', '.join(valid_platforms)}"

    result = await generate_post(
        topic=topic,
        platform_name=platform.lower(),
        tone=tone,
        target_audience=target_audience or None,
    )

    if "error" in result:
        return result["error"]

    # Save to database
    post_id = await SocialPostRepo.create(
        user_id=ctx.user_id,
        platform=result["platform"],
        content=result["content"],
        hashtags=result.get("hashtags"),
        media_suggestion=result.get("media_suggestion"),
        topic=topic,
        tone=tone,
        target_audience=target_audience or None,
    )

    # Format response
    lines = [
        f"📱 **{platform.upper()} Post** (#{post_id})",
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━",
        result["content"],
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"📌 Status: Draft | ID: #{post_id}",
    ]

    if result.get("media_suggestion"):
        lines.append(f"🖼️ Visual idea: {result['media_suggestion']}")

    lines.append("\n💡 You can edit, delete, or mark as posted using the post ID.")

    return "\n".join(lines)


@tool
async def create_multi_platform_post(
    topic: str,
    tone: str = "professional",
    target_audience: str = "",
    platforms: str = "",
    *,
    config: RunnableConfig,
) -> str:
    """Generate posts for multiple social media platforms at once from a single topic.

    Args:
        topic: What the posts should be about
        tone: Writing tone — professional, casual, inspirational, or humorous
        target_audience: Who the posts are for (e.g., "developers", "founders")
        platforms: Comma-separated platforms (e.g., "linkedin,instagram"). Empty = all platforms
    """
    ctx = get_user_context(config)

    platform_list = [p.strip().lower() for p in platforms.split(",") if p.strip()] if platforms else None

    results = await generate_multi_platform(
        topic=topic,
        tone=tone,
        target_audience=target_audience or None,
        platforms=platform_list,
    )

    if not results or (len(results) == 1 and "error" in results[0]):
        return results[0].get("error", "Failed to generate posts.")

    # Save all posts and build response
    output_lines = [f"📱 **Multi-Platform Posts Generated**\n"]

    for result in results:
        post_id = await SocialPostRepo.create(
            user_id=ctx.user_id,
            platform=result["platform"],
            content=result["content"],
            hashtags=result.get("hashtags"),
            media_suggestion=result.get("media_suggestion"),
            topic=topic,
            tone=tone,
            target_audience=target_audience or None,
        )

        output_lines.extend([
            f"━━ {result['platform'].upper()} (#{post_id}) ━━",
            result["content"],
            "",
        ])

    output_lines.append(f"\n✅ {len(results)} posts saved as drafts. Use post IDs to edit, delete, or mark as posted.")
    return "\n".join(output_lines)


@tool
async def list_social_posts(
    platform: str = "",
    status: str = "",
    *,
    config: RunnableConfig,
) -> str:
    """List saved social media posts, optionally filtered by platform or status.

    Args:
        platform: Filter by platform (linkedin, instagram, facebook, twitter). Empty = all
        status: Filter by status (draft, approved, posted, archived). Empty = all
    """
    ctx = get_user_context(config)
    posts = await SocialPostRepo.list_posts(
        ctx.user_id,
        platform=platform.lower() if platform else None,
        status=status.lower() if status else None,
    )

    if not posts:
        filters = []
        if platform:
            filters.append(f"platform={platform}")
        if status:
            filters.append(f"status={status}")
        filter_str = f" ({', '.join(filters)})" if filters else ""
        return f"No social media posts found{filter_str}."

    lines = [f"📋 **Social Media Posts** ({len(posts)} found)\n"]
    for post in posts:
        pin = " 📌" if post.get("is_pinned") else ""
        status_emoji = {"draft": "📝", "approved": "✅", "posted": "🚀", "archived": "📦"}.get(post["status"], "")
        lines.append(
            f"#{post['id']} | {post['platform'].upper()} | {status_emoji} {post['status']}{pin}\n"
            f"   {post['content'][:100]}..."
            if len(post["content"]) > 100
            else f"#{post['id']} | {post['platform'].upper()} | {status_emoji} {post['status']}{pin}\n"
                 f"   {post['content']}"
        )
    return "\n".join(lines)


@tool
async def get_social_post(post_id: int, *, config: RunnableConfig) -> str:
    """Get the full content of a specific social media post by ID.

    Args:
        post_id: The post ID number
    """
    ctx = get_user_context(config)
    post = await SocialPostRepo.get(ctx.user_id, post_id)
    if not post:
        return f"Post #{post_id} not found."

    lines = [
        f"📱 **{post['platform'].upper()} Post** (#{post['id']})",
        f"Status: {post['status']} | Tone: {post.get('tone', 'N/A')}",
        f"Topic: {post.get('topic', 'N/A')}",
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━",
        post["content"],
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━",
    ]

    if post.get("media_suggestion"):
        lines.append(f"🖼️ Visual idea: {post['media_suggestion']}")
    if post.get("hashtags"):
        lines.append(f"# Hashtags: {post['hashtags']}")
    lines.append(f"\nCreated: {post['created_at']}")

    return "\n".join(lines)


@tool
async def edit_social_post(
    post_id: int,
    edit_instruction: str,
    *,
    config: RunnableConfig,
) -> str:
    """Edit an existing social media post using AI. Describe what changes you want.

    Args:
        post_id: The post ID to edit
        edit_instruction: What to change (e.g., "make it shorter", "add more emojis", "change tone to casual")
    """
    ctx = get_user_context(config)
    post = await SocialPostRepo.get(ctx.user_id, post_id)
    if not post:
        return f"Post #{post_id} not found."

    new_content = await edit_post(
        current_content=post["content"],
        edit_instruction=edit_instruction,
        platform_name=post["platform"],
    )

    # Update in database
    await SocialPostRepo.update(ctx.user_id, post_id, content=new_content)

    # Extract updated hashtags
    hashtags = ",".join(w for w in new_content.split() if w.startswith("#"))
    if hashtags:
        await SocialPostRepo.update(ctx.user_id, post_id, hashtags=hashtags)

    return (
        f"✏️ Post #{post_id} updated!\n\n"
        f"━━ {post['platform'].upper()} ━━\n"
        f"{new_content}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )


@tool
async def delete_social_post(post_id: int, *, config: RunnableConfig) -> str:
    """Delete a social media post by ID.

    Args:
        post_id: The post ID to delete
    """
    ctx = get_user_context(config)
    success = await SocialPostRepo.delete(ctx.user_id, post_id)
    if not success:
        return f"Post #{post_id} not found."
    return f"🗑️ Post #{post_id} deleted."


@tool
async def mark_post_status(
    post_id: int,
    status: str,
    *,
    config: RunnableConfig,
) -> str:
    """Update the status of a social media post.

    Args:
        post_id: The post ID
        status: New status — one of: draft, approved, posted, archived
    """
    ctx = get_user_context(config)
    valid = ("draft", "approved", "posted", "archived")
    if status.lower() not in valid:
        return f"Invalid status '{status}'. Must be one of: {', '.join(valid)}"

    if status.lower() == "posted":
        success = await SocialPostRepo.mark_posted(ctx.user_id, post_id)
    else:
        success = await SocialPostRepo.update(ctx.user_id, post_id, status=status.lower())

    if not success:
        return f"Post #{post_id} not found."

    emoji = {"draft": "📝", "approved": "✅", "posted": "🚀", "archived": "📦"}[status.lower()]
    return f"{emoji} Post #{post_id} marked as {status}."


@tool
async def search_social_posts(query: str, *, config: RunnableConfig) -> str:
    """Search through social media post history by keyword.

    Args:
        query: Search term to find in post content, topics, or hashtags
    """
    ctx = get_user_context(config)
    posts = await SocialPostRepo.search(ctx.user_id, query)
    if not posts:
        return f"No posts found matching '{query}'."

    lines = [f"🔍 **Search results for '{query}'** ({len(posts)} found)\n"]
    for post in posts:
        lines.append(
            f"#{post['id']} | {post['platform'].upper()} | {post['status']}\n"
            f"   {post['content'][:120]}..."
        )
    return "\n".join(lines)
