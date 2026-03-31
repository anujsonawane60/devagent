from abc import ABC, abstractmethod


class InterfaceAdapter(ABC):
    """Base class for all platform adapters (Telegram, CLI, Discord, etc.)."""

    @abstractmethod
    async def start(self):
        """Start listening for messages."""
        ...

    @abstractmethod
    async def stop(self):
        """Graceful shutdown."""
        ...
