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
        assert len(handlers) == 16

    def test_handler_commands(self):
        auth = AuthManager([111])
        cmd = CommandHandler()
        handlers = create_handlers(auth, cmd)
        commands = [h.commands for h in handlers]
        assert frozenset({"help"}) in commands
        assert frozenset({"status"}) in commands
        assert frozenset({"analyze"}) in commands
        assert frozenset({"index"}) in commands
        assert frozenset({"search"}) in commands
        assert frozenset({"find"}) in commands
        assert frozenset({"generate"}) in commands
        assert frozenset({"diff"}) in commands
        assert frozenset({"validate"}) in commands
        assert frozenset({"undo"}) in commands
        assert frozenset({"add"}) in commands
        assert frozenset({"fix"}) in commands
        assert frozenset({"deploy"}) in commands
        assert frozenset({"errors"}) in commands
        assert frozenset({"pr"}) in commands
        assert frozenset({"setup"}) in commands


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

    @pytest.mark.asyncio
    async def test_search_handler(self):
        auth = AuthManager([123])
        cmd = CommandHandler()
        handlers = create_handlers(auth, cmd)
        search_handler = [h for h in handlers if "search" in h.commands][0]

        update = MagicMock()
        update.effective_user.id = 123
        update.message.reply_text = AsyncMock()
        context = MagicMock()
        context.args = ["test"]

        await search_handler.callback(update, context)
        update.message.reply_text.assert_called_once()
        # Should indicate no DB available since we didn't set one up
        assert "not available" in update.message.reply_text.call_args[0][0].lower()

    @pytest.mark.asyncio
    async def test_generate_handler(self):
        auth = AuthManager([123])
        cmd = CommandHandler()
        handlers = create_handlers(auth, cmd)
        gen_handler = [h for h in handlers if "generate" in h.commands][0]

        update = MagicMock()
        update.effective_user.id = 123
        update.message.reply_text = AsyncMock()
        context = MagicMock()
        context.args = ["add", "login"]

        await gen_handler.callback(update, context)
        update.message.reply_text.assert_called_once()
        assert "not configured" in update.message.reply_text.call_args[0][0].lower()

    @pytest.mark.asyncio
    async def test_diff_handler(self):
        auth = AuthManager([123])
        cmd = CommandHandler()
        handlers = create_handlers(auth, cmd)
        diff_handler = [h for h in handlers if "diff" in h.commands][0]

        update = MagicMock()
        update.effective_user.id = 123
        update.message.reply_text = AsyncMock()
        context = MagicMock()
        context.args = []

        await diff_handler.callback(update, context)
        update.message.reply_text.assert_called_once()
        assert "Usage" in update.message.reply_text.call_args[0][0]

    @pytest.mark.asyncio
    async def test_deploy_handler(self):
        auth = AuthManager([123])
        cmd = CommandHandler()
        handlers = create_handlers(auth, cmd)
        deploy_handler = [h for h in handlers if "deploy" in h.commands][0]

        update = MagicMock()
        update.effective_user.id = 123
        update.message.reply_text = AsyncMock()
        context = MagicMock()
        context.args = ["staging"]

        await deploy_handler.callback(update, context)
        update.message.reply_text.assert_called_once()
        assert "vercel not configured" in update.message.reply_text.call_args[0][0].lower()

    @pytest.mark.asyncio
    async def test_errors_handler(self):
        auth = AuthManager([123])
        cmd = CommandHandler()
        handlers = create_handlers(auth, cmd)
        errors_handler = [h for h in handlers if "errors" in h.commands][0]

        update = MagicMock()
        update.effective_user.id = 123
        update.message.reply_text = AsyncMock()
        context = MagicMock()

        await errors_handler.callback(update, context)
        update.message.reply_text.assert_called_once()
        assert "sentry not configured" in update.message.reply_text.call_args[0][0].lower()

    @pytest.mark.asyncio
    async def test_setup_handler(self):
        auth = AuthManager([123])
        cmd = CommandHandler()
        handlers = create_handlers(auth, cmd)
        setup_handler = [h for h in handlers if "setup" in h.commands][0]

        update = MagicMock()
        update.effective_user.id = 123
        update.message.reply_text = AsyncMock()
        context = MagicMock()
        context.args = []

        await setup_handler.callback(update, context)
        update.message.reply_text.assert_called_once()
        assert "Usage" in update.message.reply_text.call_args[0][0]
