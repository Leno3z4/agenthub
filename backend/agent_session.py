import secrets
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from typing import Any

import redis

from config import SESSION_REDIS_URL, SESSION_TTL_SECONDS


class SessionStore(ABC):
    """Storage abstraction for agent sessions."""

    @abstractmethod
    def save(self, token: str, session: dict[str, Any], ttl: timedelta) -> None:
        raise NotImplementedError

    @abstractmethod
    def get(self, token: str) -> dict[str, Any] | None:
        raise NotImplementedError

    @abstractmethod
    def touch(self, token: str, last_seen: datetime) -> None:
        raise NotImplementedError

    @abstractmethod
    def delete(self, token: str) -> None:
        raise NotImplementedError


class RedisSessionStore(SessionStore):
    """Redis-backed session storage with key-level TTL expiration."""

    def __init__(
        self,
        redis_url: str,
        key_prefix: str = "alias:session:",
    ) -> None:
        self._redis = redis.Redis.from_url(redis_url, decode_responses=True)
        self._key_prefix = key_prefix

    def _key(self, token: str) -> str:
        return f"{self._key_prefix}{token}"

    def save(self, token: str, session: dict[str, Any], ttl: timedelta) -> None:
        expires = session["expires"]
        last_seen = session["last_seen"]
        ttl_seconds = max(1, int(ttl.total_seconds()))

        self._redis.hset(
            self._key(token),
            mapping={
                "api_key": session["api_key"],
                "expires": expires.isoformat(),
                "last_seen": last_seen.isoformat(),
            },
        )
        self._redis.expire(self._key(token), ttl_seconds)

    def get(self, token: str) -> dict[str, Any] | None:
        values = self._redis.hgetall(self._key(token))
        if not values:
            return None

        return {
            "api_key": values["api_key"],
            "expires": datetime.fromisoformat(values["expires"]),
            "last_seen": datetime.fromisoformat(values["last_seen"]),
        }

    def touch(self, token: str, last_seen: datetime) -> None:
        # HSET preserves the existing Redis TTL, so touching a session does
        # not turn the fixed 30-day session lifetime into a sliding lifetime.
        self._redis.hset(
            self._key(token),
            "last_seen",
            last_seen.isoformat(),
        )

    def delete(self, token: str) -> None:
        self._redis.delete(self._key(token))


SESSION_DURATION = timedelta(seconds=SESSION_TTL_SECONDS)
_session_store: SessionStore = RedisSessionStore(SESSION_REDIS_URL)


def create_session(api_key: str) -> str:
    token = secrets.token_urlsafe(48)
    now = datetime.now(timezone.utc)

    _session_store.save(
        token,
        {
            "api_key": api_key,
            "expires": now + SESSION_DURATION,
            "last_seen": now,
        },
        SESSION_DURATION,
    )
    return token


def validate_session(token: str) -> bool:
    session = _session_store.get(token)
    if session is None:
        return False

    if session["expires"] < datetime.now(timezone.utc):
        _session_store.delete(token)
        return False

    _session_store.touch(token, datetime.now(timezone.utc))
    return True


def touch_session(token: str) -> None:
    if _session_store.get(token):
        _session_store.touch(token, datetime.now(timezone.utc))


def destroy_session(token: str) -> None:
    _session_store.delete(token)


def session_info(token: str) -> dict[str, Any] | None:
    return _session_store.get(token)
