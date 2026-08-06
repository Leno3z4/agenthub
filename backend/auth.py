import hashlib
import os
import secrets

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token


def generate_api_key() -> tuple[str, str]:
    """Returns (plaintext_key, hash_to_store). Plaintext is shown to
    the caller exactly once, at /wallet/link time — never stored or
    retrievable again, only its hash is kept for comparison."""
    key = secrets.token_urlsafe(32)
    return key, hash_api_key(key)


def hash_api_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


def verify_api_key(key: str | None, stored_hash: str | None) -> bool:
    if not key or not stored_hash:
        return False
    return secrets.compare_digest(hash_api_key(key), stored_hash)


def generate_nonce() -> str:
    return secrets.token_urlsafe(32)


def hash_nonce(nonce: str) -> str:
    return hashlib.sha256(nonce.encode()).hexdigest()


def verify_google_id_token(id_token_value: str) -> dict:
    """Verify a Google ID token and return its trusted claims."""
    if not id_token_value:
        raise ValueError("Google ID token is required.")

    audience = os.getenv("GOOGLE_CLIENT_ID")
    if not audience:
        raise RuntimeError("GOOGLE_CLIENT_ID is not configured.")

    claims = google_id_token.verify_oauth2_token(
        id_token_value,
        google_requests.Request(),
        audience,
    )

    if claims.get("iss") not in {
        "accounts.google.com",
        "https://accounts.google.com",
    }:
        raise ValueError("Invalid Google token issuer.")

    if not claims.get("sub"):
        raise ValueError("Google token has no subject.")

    if claims.get("email_verified") is False:
        raise ValueError("Google email is not verified.")

    return claims
