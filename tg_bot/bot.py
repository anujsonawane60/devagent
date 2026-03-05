"""Telegram bot application builder."""

import logging

from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes

from agent.commands import CommandHandler
from config.llm import create_llm_provider
from config.settings import Settings
from integrations.github import GitHubManager
from integrations.sentry import SentryClient
from integrations.vercel import VercelClient
from storage.db import Database
from tg_bot.auth import AuthManager
from tg_bot.handlers import create_handlers

logger = logging.getLogger(__name__)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send errors to the user instead of crashing silently."""
    logger.error("Exception while handling an update:", exc_info=context.error)
    if isinstance(update, Update) and update.message:
        error_name = type(context.error).__name__
        error_msg = str(context.error)
        # Truncate long error messages for Telegram
        if len(error_msg) > 300:
            error_msg = error_msg[:300] + "..."
        await update.message.reply_text(f"Error: {error_name}\n{error_msg}")


def create_bot(settings: Settings, db: Database | None = None) -> "Application":
    """Build and configure the Telegram bot application with all integrations."""
    auth_manager = AuthManager(settings.telegram_allowed_users)

    # Create LLM provider
    llm = None
    try:
        api_key = settings.get_llm_api_key()
        if api_key:
            llm = create_llm_provider(settings.llm_provider, api_key, settings.get_llm_model())
    except Exception:
        pass

    # Create GitHub manager
    github = None
    if settings.github_token:
        github = GitHubManager(token=settings.github_token)

    # Create Sentry client
    sentry = None
    if settings.sentry_auth_token and settings.sentry_org and settings.sentry_project:
        sentry = SentryClient(
            auth_token=settings.sentry_auth_token,
            org_slug=settings.sentry_org,
            project_slug=settings.sentry_project,
        )

    # Create Vercel client
    vercel = None
    if settings.vercel_token:
        vercel = VercelClient(
            token=settings.vercel_token,
            project_id=settings.vercel_project_id,
            team_id=settings.vercel_team_id,
        )

    command_handler = CommandHandler(
        db=db,
        llm=llm,
        github=github,
        sentry=sentry,
        vercel=vercel,
    )

    app = ApplicationBuilder().token(settings.telegram_bot_token).build()

    for handler in create_handlers(auth_manager, command_handler):
        app.add_handler(handler)

    app.add_error_handler(error_handler)

    return app
