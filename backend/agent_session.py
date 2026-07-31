import secrets
from datetime import datetime, timedelta

_sessions: dict[str, dict] = {}

SESSION_DURATION = timedelta(days=30)


def create_session(api_key: str) -> str:
    token = secrets.token_urlsafe(48)

    _sessions[token] = {
        "api_key": api_key,
        "expires": datetime.utcnow() + SESSION_DURATION,
        "last_seen": datetime.utcnow(),
    }

    return token


def validate_session(token: str) -> bool:
    session = _sessions.get(token)

    if session is None:
        return False

    if session["expires"] < datetime.utcnow():
        del _sessions[token]
        return False

    session["last_seen"] = datetime.utcnow()
    return True


def touch_session(token: str):
    session = _sessions.get(token)

    if session:
        session["last_seen"] = datetime.utcnow()


def destroy_session(token: str):
    _sessions.pop(token, None)


def session_info(token: str):
    return _sessions.get(token)
