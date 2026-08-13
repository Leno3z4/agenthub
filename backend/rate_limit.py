import time
from collections import defaultdict
from threading import Lock

from fastapi import HTTPException, Request


class RateLimiter:
    def __init__(self):
        self._requests = defaultdict(list)
        self._lock = Lock()

    def check(self, key: str, limit: int, window: int = 60):
        now = time.monotonic()

        with self._lock:
            requests = self._requests[key]

            cutoff = now - window
            requests[:] = [timestamp for timestamp in requests if timestamp > cutoff]

            if len(requests) >= limit:
                raise HTTPException(
                    status_code=429,
                    detail="Too many requests. Please try again later.",
                    headers={"Retry-After": str(window)},
                )

            requests.append(now)


limiter = RateLimiter()


def rate_limit(
    request: Request,
    *,
    limit: int,
    window: int = 60,
    identity: str | None = None,
):
    ip = request.client.host if request.client else "unknown"

    if identity:
        key = f"{ip}:{identity}"
    else:
        key = ip

    limiter.check(
        key,
        limit=limit,
        window=window,
    )
