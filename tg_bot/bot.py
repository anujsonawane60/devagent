"""Telegram bot application builder."""

from telegram.ext import ApplicationBuilder

from agent.commands import CommandHandler
from config.settings import Settings
from tg_bot.auth import AuthManager
from tg_bot.handlers import create_handlers


def create_bot(settings: Settings) -> "Application":
    """Build and configure the Telegram bot application."""
    auth_manager = AuthManager(settings.telegram_allowed_users)
    command_handler = CommandHandler()

    app = ApplicationBuilder().token(settings.telegram_bot_token).build()

    for handler in create_handlers(auth_manager, command_handler):
        app.add_handler(handler)

    return app
