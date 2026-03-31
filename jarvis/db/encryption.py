"""
AES-256 encryption layer for sensitive data (Fernet = AES-128-CBC + HMAC).

Usage:
    from jarvis.db.encryption import encrypt, decrypt

    encrypted = encrypt("9876543210")    # → "gAAAAABk3x..."
    original  = decrypt(encrypted)        # → "9876543210"

The encryption key lives in .env (ENCRYPTION_KEY). If not set,
a key is auto-generated on first run and printed for the user to save.
"""

import logging
from cryptography.fernet import Fernet

from jarvis.config import settings

logger = logging.getLogger(__name__)

_fernet: Fernet | None = None
_warned_no_key: bool = False


def _get_fernet() -> Fernet:
    global _fernet, _warned_no_key
    if _fernet is None:
        key = settings.ENCRYPTION_KEY
        if not key:
            key = Fernet.generate_key().decode()
            if not _warned_no_key:
                _warned_no_key = True
                logger.warning(
                    "No ENCRYPTION_KEY in .env! Auto-generated for this session. "
                    "Save this to your .env or you will lose access to encrypted data: "
                    f"ENCRYPTION_KEY={key}"
                )
        _fernet = Fernet(key.encode() if isinstance(key, str) else key)
    return _fernet


def encrypt(plaintext: str) -> str:
    """Encrypt a string. Returns base64-encoded ciphertext."""
    if not plaintext:
        return ""
    f = _get_fernet()
    return f.encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    """Decrypt a base64-encoded ciphertext. Returns plaintext string."""
    if not ciphertext:
        return ""
    f = _get_fernet()
    return f.decrypt(ciphertext.encode()).decode()


def generate_key() -> str:
    """Generate a new Fernet encryption key. Run once, save to .env."""
    return Fernet.generate_key().decode()
