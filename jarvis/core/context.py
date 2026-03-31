from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class UserContext:
    """Identity and context for the current user, created by interface adapters."""

    user_id: str
    chat_id: str
    platform: str  # "telegram", "cli", "discord", etc.
    username: Optional[str] = None
    display_name: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "chat_id": self.chat_id,
            "platform": self.platform,
            "username": self.username,
            "display_name": self.display_name,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "UserContext":
        return cls(**data)
