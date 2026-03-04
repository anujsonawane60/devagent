"""Telegram bot authentication via user whitelist."""

import functools
import logging
from typing import Callable, Set

from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


class AuthManager:
    def __init__(self, allowed_users: list[int] | None = None):
        self._allowed: Set[int] = set(allowed_users or [])

    def is_authorized(self, user_id: int) -> bool:
        return user_id in self._allowed

    def add_user(self, user_id: int) -> None:
        self._allowed.add(user_id)

    def remove_user(self, user_id: int) -> None:
        self._allowed.discard(user_id)

    @property
    def allowed_users(self) -> Set[int]:
        return self._allowed.copy()


def require_auth(auth_manager: AuthManager) -> Callable:
    """Decorator that restricts handler to authorized users only."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            user_id = update.effective_user.id
            if not auth_manager.is_authorized(user_id):
                logger.warning(f"Unauthorized access attempt by user {user_id}")
                await update.message.reply_text("Unauthorized. Access denied.")
                return
            return await func(update, context)
        return wrapper
    return decorator
