from google.oauth2 import id_token
from google.auth.transport import requests
from fastapi import HTTPException


def verify_google_token(token: str) -> dict:
    try:
        info = id_token.verify_oauth2_token(
            token,
            requests.Request(),
        )
    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid Google identity token",
        )

    if not info.get("sub"):
        raise HTTPException(
            status_code=401,
            detail="Google token has no subject",
        )

    return info
