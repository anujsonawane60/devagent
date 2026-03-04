"""Telegram command handler wiring."""

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler as TGCommandHandler

from agent.commands import CommandHandler
from tg_bot.auth import AuthManager, require_auth


def create_handlers(auth_manager: AuthManager, command_handler: CommandHandler) -> list:
    """Create and return all telegram command handlers."""

    @require_auth(auth_manager)
    async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(command_handler.help())

    @require_auth(auth_manager)
    async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(command_handler.status())

    @require_auth(auth_manager)
    async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        path = " ".join(context.args) if context.args else ""
        await update.message.reply_text(command_handler.analyze(path))

    return [
        TGCommandHandler("help", help_command),
        TGCommandHandler("status", status_command),
        TGCommandHandler("analyze", analyze_command),
    ]
