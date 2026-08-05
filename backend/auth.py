import hashlib
import secrets


def generate_api_key() -> tuple[str, str]:
    """Return a plaintext API key and the hash stored for verification."""
    key = secrets.token_urlsafe(32)
    return key, hash_api_key(key)


def hash_api_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


def verify_api_key(key: str | None, stored_hash: str | None) -> bool:
    if not key or not stored_hash:
        return False
    return secrets.compare_digest(hash_api_key(key), stored_hash)
