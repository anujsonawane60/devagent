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

    @require_auth(auth_manager)
    async def validate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        path = " ".join(context.args) if context.args else ""
        result = await command_handler.validate(path)
        await update.message.reply_text(result)

    @require_auth(auth_manager)
    async def undo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        path = " ".join(context.args) if context.args else ""
        await update.message.reply_text(command_handler.undo(path))

    @require_auth(auth_manager)
    async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        description = " ".join(context.args) if context.args else ""
        result = await command_handler.add_feature(description, project_path="")
        await update.message.reply_text(result)

    @require_auth(auth_manager)
    async def fix_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        issue_id = " ".join(context.args) if context.args else ""
        result = await command_handler.fix_error(issue_id, project_path="")
        await update.message.reply_text(result)

    @require_auth(auth_manager)
    async def deploy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        env = " ".join(context.args) if context.args else ""
        result = await command_handler.deploy(env, project_path="")
        await update.message.reply_text(result)

    @require_auth(auth_manager)
    async def errors_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        result = await command_handler.errors()
        await update.message.reply_text(result)

    @require_auth(auth_manager)
    async def pr_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        title = " ".join(context.args) if context.args else ""
        result = await command_handler.create_pr(title, project_path="")
        await update.message.reply_text(result)

    @require_auth(auth_manager)
    async def setup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        path = " ".join(context.args) if context.args else ""
        result = await command_handler.setup_project(path)
        await update.message.reply_text(result)

    return [
        TGCommandHandler("help", help_command),
        TGCommandHandler("status", status_command),
        TGCommandHandler("analyze", analyze_command),
        TGCommandHandler("index", index_command),
        TGCommandHandler("search", search_command),
        TGCommandHandler("find", find_command),
        TGCommandHandler("generate", generate_command),
        TGCommandHandler("diff", diff_command),
        TGCommandHandler("validate", validate_command),
        TGCommandHandler("undo", undo_command),
        TGCommandHandler("add", add_command),
        TGCommandHandler("fix", fix_command),
        TGCommandHandler("deploy", deploy_command),
        TGCommandHandler("errors", errors_command),
        TGCommandHandler("pr", pr_command),
        TGCommandHandler("setup", setup_command),
    ]
