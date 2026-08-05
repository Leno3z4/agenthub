import hashlib
import secrets


def generate_api_key() -> tuple[str, str]:
    """Returns (plaintext_key, hash_to_store). Plaintext is shown to
    the caller exactly once, at /wallet/link time — never stored or
    retrievable again, only its hash is kept for comparison."""
    key = secrets.token_urlsafe(32)
    return key, hash_api_key(key)


def hash_api_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


def verify_api_key(key: str, stored_hash: str) -> bool:
    return secrets.compare_digest(hash_api_key(key), stored_hash)
