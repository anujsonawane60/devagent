import logging
import tempfile
from pathlib import Path

from openai import OpenAI
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

from jarvis.agents.supervisor import run_supervisor
from jarvis.core.context import UserContext
from jarvis.auth.authenticator import Authenticator
from jarvis.db.repositories import ConversationRepo, UserRepo
from jarvis.config import settings

logger = logging.getLogger(__name__)
auth = Authenticator()


def _build_user_context(update: Update) -> UserContext:
    user = update.effective_user
    return UserContext(
        user_id=str(user.id),
        chat_id=str(update.effective_chat.id),
        platform="telegram",
        username=user.username,
        display_name=user.full_name,
    )


async def _transcribe_voice(update: Update) -> str | None:
    """Download voice/audio from Telegram and transcribe with OpenAI Whisper."""
    voice = update.message.voice or update.message.audio
    if not voice:
        return None

    try:
        file = await voice.get_file()

        # Download to a temp file
        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
            tmp_path = tmp.name
            await file.download_to_drive(tmp_path)

        # Transcribe with Whisper
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        with open(tmp_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
            )

        # Clean up temp file
        Path(tmp_path).unlink(missing_ok=True)

        text = transcript.text.strip()
        if text:
            logger.info(f"Transcribed voice ({voice.duration}s): {text[:100]}")
            return text
        return None

    except Exception as e:
        logger.error(f"Voice transcription failed: {e}")
        Path(tmp_path).unlink(missing_ok=True)
        return None


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ctx = _build_user_context(update)
    if not auth.is_authorized(ctx.user_id, ctx.platform):
        await update.message.reply_text("Sorry, you are not authorized to use this bot.")
        return
    await update.message.reply_text(
        "Hello! I'm JARVIS, your personal AI assistant.\n\n"
        "I can help you with:\n"
        "- Managing tasks and reminders\n"
        "- Searching the web\n"
        "- Saving and recalling notes\n"
        "- Telling you the time anywhere in the world\n\n"
        "Just talk to me naturally — text or voice!"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "**JARVIS Commands:**\n"
        "/start - Welcome message\n"
        "/help - Show this help\n"
        "/clear - Clear conversation history\n\n"
        "**What I can do:**\n"
        '- "Remind me to call mom tomorrow"\n'
        '- "Search for latest tech news"\n'
        '- "Save a note about my meeting"\n'
        '- "What time is it in Tokyo?"\n'
        '- "Show my tasks"\n\n'
        "Send text or voice messages — I understand both!",
        parse_mode="Markdown",
    )


async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ctx = _build_user_context(update)
    await ConversationRepo.clear_history(ctx.chat_id)
    await update.message.reply_text("Conversation history cleared. Fresh start!")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    ctx = _build_user_context(update)

    # Auth check
    if not auth.is_authorized(ctx.user_id, ctx.platform):
        await update.message.reply_text("Sorry, you are not authorized to use this bot.")
        return

    # Track user
    await UserRepo.upsert(ctx.user_id, ctx.platform, ctx.username, ctx.display_name)

    # Get text — from text message or voice transcription
    user_message = update.message.text

    if not user_message and (update.message.voice or update.message.audio):
        await update.message.chat.send_action("typing")
        user_message = await _transcribe_voice(update)
        if not user_message:
            await update.message.reply_text("Sorry, I couldn't understand that voice message. Could you try again?")
            return

    if not user_message:
        return

    logger.info(f"[{ctx.user_id}] User: {user_message[:100]}")

    # Show typing indicator
    await update.message.chat.send_action("typing")

    try:
        response = await run_supervisor(ctx, user_message)
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
    # Handle text messages, voice notes, and audio messages
    app.add_handler(MessageHandler(
        (filters.TEXT | filters.VOICE | filters.AUDIO) & ~filters.COMMAND,
        handle_message,
    ))

    return app
