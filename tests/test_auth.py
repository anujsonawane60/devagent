"""Tests for tg_bot/auth.py"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from tg_bot.auth import AuthManager, require_auth


class TestAuthManager:
    def test_authorized_user(self):
        auth = AuthManager([111, 222])
        assert auth.is_authorized(111) is True

    def test_unauthorized_user(self):
        auth = AuthManager([111])
        assert auth.is_authorized(999) is False

    def test_add_user(self):
        auth = AuthManager()
        auth.add_user(555)
        assert auth.is_authorized(555) is True

    def test_remove_user(self):
        auth = AuthManager([111])
        auth.remove_user(111)
        assert auth.is_authorized(111) is False

    def test_allowed_users_returns_copy(self):
        auth = AuthManager([1, 2, 3])
        users = auth.allowed_users
        users.add(999)
        assert 999 not in auth.allowed_users


class TestRequireAuth:
    @pytest.mark.asyncio
    async def test_allows_authorized(self):
        auth = AuthManager([123])

        @require_auth(auth)
        async def handler(update, context):
            return "ok"

        update = MagicMock()
        update.effective_user.id = 123
        result = await handler(update, MagicMock())
        assert result == "ok"

    @pytest.mark.asyncio
    async def test_blocks_unauthorized(self):
        auth = AuthManager([123])

        @require_auth(auth)
        async def handler(update, context):
            return "ok"

        update = MagicMock()
        update.effective_user.id = 999
        update.message.reply_text = AsyncMock()
        result = await handler(update, MagicMock())
        assert result is None
        update.message.reply_text.assert_called_once_with("Unauthorized. Access denied.")
