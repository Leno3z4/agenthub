import hashlib
import logging
import secrets

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token

from config import GOOGLE_CLIENT_ID

logger = logging.getLogger("alias.auth")

GOOGLE_ISSUERS = {
    "accounts.google.com",
    "https://accounts.google.com",
}


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


def verify_google_id_token(id_token_value: str) -> dict[str, str | None]:
    """Verify a Google ID token and return only trusted identity claims.

    google-auth verifies the token signature, expiry, and configured audience.
    The explicit issuer and email checks below keep authentication fail-closed.
    Frontend profile fields are never used as an identity source.
    """
    if not isinstance(id_token_value, str) or not id_token_value:
        logger.warning("google_token_rejected reason=missing_token")
        raise ValueError("Authentication failed.")

    if not GOOGLE_CLIENT_ID:
        logger.error("google_token_rejected reason=missing_client_configuration")
        raise RuntimeError("Authentication service is not configured.")

    try:
        verified_claims = google_id_token.verify_oauth2_token(
            id_token_value,
            google_requests.Request(),
            GOOGLE_CLIENT_ID,
        )
    except Exception as exc:
        # Do not log the token or exception text: either can contain sensitive
        # token material or provider-specific details.
        logger.warning("google_token_rejected reason=verification_failed")
        raise ValueError("Authentication failed.") from exc

    if verified_claims.get("iss") not in GOOGLE_ISSUERS:
        logger.warning("google_token_rejected reason=invalid_issuer")
        raise ValueError("Authentication failed.")

    subject = verified_claims.get("sub")
    email = verified_claims.get("email")
    if (
        not isinstance(subject, str)
        or not subject
        or not isinstance(email, str)
        or not email
        or verified_claims.get("email_verified") is not True
    ):
        logger.warning("google_token_rejected reason=missing_verified_identity")
        raise ValueError("Authentication failed.")

    # Return only the fields the application is allowed to use. These values
    # are read after signature, expiry, issuer, and audience verification.
    return {
        "sub": subject,
        "email": email,
        "name": verified_claims.get("name")
        if isinstance(verified_claims.get("name"), str)
        else None,
        "picture": verified_claims.get("picture")
        if isinstance(verified_claims.get("picture"), str)
        else None,
    }
