import hashlib
import logging
import secrets

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token

from config import GOOGLE_CLIENT_ID

logger = logging.getLogger("alias.auth")


def generate_api_key() -> tuple[str, str]:
    """Return a one-time plaintext API key and its stored hash."""
    key = secrets.token_urlsafe(32)
    return key, hash_api_key(key)


def hash_api_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


def verify_api_key(key: str | None, stored_hash: str | None) -> bool:
    if not key or not stored_hash:
        return False
    return secrets.compare_digest(hash_api_key(key), stored_hash)


def generate_nonce() -> str:
    """Generate a 256-bit nonce for one wallet-authentication attempt."""
    return secrets.token_urlsafe(32)


def hash_nonce(nonce: str) -> str:
    return hashlib.sha256(nonce.encode()).hexdigest()


def verify_google_id_token(id_token_value: str) -> dict:
    """Verify a Google ID token and return only trusted Google claims.

    google-auth verifies the token signature, expiry, issuer, and audience.
    The explicit issuer, subject, email, and email_verified checks below
    keep registration fail-closed and ensure frontend profile fields are
    never used as an identity source.
    """
    if not id_token_value:
        logger.warning("google_token_rejected reason=missing_token")
        raise ValueError("Authentication failed.")

    if not GOOGLE_CLIENT_ID:
        logger.error("google_token_rejected reason=missing_client_configuration")
        raise RuntimeError("Authentication service is not configured.")

    try:
        claims = google_id_token.verify_oauth2_token(
            id_token_value,
            google_requests.Request(),
            GOOGLE_CLIENT_ID,
        )
    except Exception as exc:
        # Do not log the token or exception text: either can contain sensitive
        # token material or provider-specific details.
        logger.warning("google_token_rejected reason=verification_failed")
        raise ValueError("Authentication failed.") from exc

    if claims.get("iss") not in {
        "accounts.google.com",
        "https://accounts.google.com",
    }:
        logger.warning("google_token_rejected reason=invalid_issuer")
        raise ValueError("Authentication failed.")

    subject = claims.get("sub")
    email = claims.get("email")
    if not subject or not email or claims.get("email_verified") is not True:
        logger.warning("google_token_rejected reason=missing_verified_identity")
        raise ValueError("Authentication failed.")

    return claims
