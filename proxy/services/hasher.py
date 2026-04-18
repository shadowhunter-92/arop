"""
SHA-256 hashing for prompts and responses.

When hash_payloads=True (default), only hashes are stored — the plaintext never
reaches the database. Two identical prompts produce the same hash, which enables
deduplication and replay matching without retaining the original text.
"""
import hashlib
import json
from typing import Any


def hash_content(content: Any) -> str:
    """Return the SHA-256 hex digest of any JSON-serialisable value."""
    serialised = json.dumps(content, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(serialised.encode("utf-8")).hexdigest()


def hash_string(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
