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

    @require_auth(auth_manager)
    async def index_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        path = " ".join(context.args) if context.args else ""
        result = await command_handler.index(path)
        await update.message.reply_text(result)

    @require_auth(auth_manager)
    async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = " ".join(context.args) if context.args else ""
        result = await command_handler.search(query)
        await update.message.reply_text(result)

    @require_auth(auth_manager)
    async def find_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        name = " ".join(context.args) if context.args else ""
        result = await command_handler.find(name)
        await update.message.reply_text(result)

    @require_auth(auth_manager)
    async def generate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        task = " ".join(context.args) if context.args else ""
        result = await command_handler.generate(task, project_path="")
        await update.message.reply_text(result)

    @require_auth(auth_manager)
    async def diff_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        path = " ".join(context.args) if context.args else ""
        await update.message.reply_text(command_handler.diff(path))

    return [
        TGCommandHandler("help", help_command),
        TGCommandHandler("status", status_command),
        TGCommandHandler("analyze", analyze_command),
        TGCommandHandler("index", index_command),
        TGCommandHandler("search", search_command),
        TGCommandHandler("find", find_command),
        TGCommandHandler("generate", generate_command),
        TGCommandHandler("diff", diff_command),
    ]
