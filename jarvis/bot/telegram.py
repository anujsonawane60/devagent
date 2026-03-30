import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

from jarvis.brain.agent import run_agent
from jarvis.config import settings

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hello! I'm JARVIS, your personal AI assistant.\n\n"
        "I can help you with:\n"
        "- Managing tasks and reminders\n"
        "- Searching the web\n"
        "- Saving and recalling notes\n"
        "- Telling you the time anywhere in the world\n\n"
        "Just talk to me naturally. How can I help you today?"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "**JARVIS Commands:**\n"
        "/start - Welcome message\n"
        "/help - Show this help\n"
        "/clear - Clear conversation history\n\n"
        "**What I can do:**\n"
        "- \"Remind me to call mom tomorrow\"\n"
        "- \"Search for latest tech news\"\n"
        "- \"Save a note about my meeting\"\n"
        "- \"What time is it in Tokyo?\"\n"
        "- \"Show my tasks\"\n\n"
        "Just type naturally!",
        parse_mode="Markdown",
    )


async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from jarvis.brain.memory import clear_history
    chat_id = str(update.effective_chat.id)
    await clear_history(chat_id)
    await update.message.reply_text("Conversation history cleared. Fresh start!")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    chat_id = str(update.effective_chat.id)
    user_message = update.message.text

    logger.info(f"[{chat_id}] User: {user_message[:100]}")

    # Show typing indicator
    await update.message.chat.send_action("typing")

    try:
        response = await run_agent(chat_id, user_message)
        # Telegram has a 4096 char limit per message
        if len(response) > 4096:
            for i in range(0, len(response), 4096):
                await update.message.reply_text(response[i : i + 4096])
        else:
            await update.message.reply_text(response)
    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        await update.message.reply_text(
            "Sorry, I encountered an error processing your request. Please try again."
        )


def create_bot_app() -> Application:
    app = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("clear", clear_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    return app
