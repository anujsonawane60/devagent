"""In-memory TTL cache."""

import time
from typing import Any


class TTLCache:
    def __init__(self, default_ttl: int = 300):
        self._store: dict[str, tuple[Any, float]] = {}
        self.default_ttl = default_ttl

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        expires_at = time.time() + (ttl if ttl is not None else self.default_ttl)
        self._store[key] = (value, expires_at)

    def get(self, key: str) -> Any | None:
        if key not in self._store:
            return None
        value, expires_at = self._store[key]
        if time.time() > expires_at:
            del self._store[key]
            return None
        return value

    def clear(self) -> None:
        self._store.clear()

    def __len__(self) -> int:
        # Prune expired entries
        now = time.time()
        self._store = {k: v for k, v in self._store.items() if v[1] > now}
        return len(self._store)
