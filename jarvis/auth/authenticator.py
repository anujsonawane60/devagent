from jarvis.config import settings


class Authenticator:
    """Simple allowlist-based authentication."""

    @staticmethod
    def is_authorized(user_id: str, platform: str) -> bool:
        if platform == "telegram":
            # Empty allowlist = allow everyone (dev mode)
            if not settings.TELEGRAM_ALLOWED_USERS:
                return True
            return user_id in settings.TELEGRAM_ALLOWED_USERS
        # CLI and other local interfaces are always authorized
        return True
