"""Tests for tg_bot/bot.py and tg_bot/handlers.py"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agent.commands import CommandHandler
from tg_bot.auth import AuthManager
from tg_bot.handlers import create_handlers


class TestCreateHandlers:
    def test_returns_handlers(self):
        auth = AuthManager([111])
        cmd = CommandHandler()
        handlers = create_handlers(auth, cmd)
        assert len(handlers) == 3

    def test_handler_commands(self):
        auth = AuthManager([111])
        cmd = CommandHandler()
        handlers = create_handlers(auth, cmd)
        commands = [h.commands for h in handlers]
        assert frozenset({"help"}) in commands
        assert frozenset({"status"}) in commands
        assert frozenset({"analyze"}) in commands


class TestHandlerExecution:
    @pytest.mark.asyncio
    async def test_help_handler(self):
        auth = AuthManager([123])
        cmd = CommandHandler()
        handlers = create_handlers(auth, cmd)
        help_handler = [h for h in handlers if "help" in h.commands][0]

        update = MagicMock()
        update.effective_user.id = 123
        update.message.reply_text = AsyncMock()
        context = MagicMock()

        await help_handler.callback(update, context)
        update.message.reply_text.assert_called_once()
        assert "/help" in update.message.reply_text.call_args[0][0]

    @pytest.mark.asyncio
    async def test_status_handler(self):
        auth = AuthManager([123])
        cmd = CommandHandler()
        handlers = create_handlers(auth, cmd)
        status_handler = [h for h in handlers if "status" in h.commands][0]

        update = MagicMock()
        update.effective_user.id = 123
        update.message.reply_text = AsyncMock()
        context = MagicMock()

        await status_handler.callback(update, context)
        update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_unauthorized_handler(self):
        auth = AuthManager([123])
        cmd = CommandHandler()
        handlers = create_handlers(auth, cmd)
        help_handler = [h for h in handlers if "help" in h.commands][0]

        update = MagicMock()
        update.effective_user.id = 999
        update.message.reply_text = AsyncMock()
        context = MagicMock()

        await help_handler.callback(update, context)
        update.message.reply_text.assert_called_once_with("Unauthorized. Access denied.")
