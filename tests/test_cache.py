"""Tests for storage/cache.py"""

import time
from unittest.mock import patch

from storage.cache import TTLCache


class TestTTLCache:
    def test_set_and_get(self):
        cache = TTLCache()
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_get_missing_key(self):
        cache = TTLCache()
        assert cache.get("nonexistent") is None

    def test_expiry(self):
        cache = TTLCache(default_ttl=1)
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        with patch("storage.cache.time") as mock_time:
            mock_time.time.return_value = time.time() + 2
            assert cache.get("key1") is None

    def test_clear(self):
        cache = TTLCache()
        cache.set("a", 1)
        cache.set("b", 2)
        assert len(cache) == 2
        cache.clear()
        assert len(cache) == 0
