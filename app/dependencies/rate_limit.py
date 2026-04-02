from __future__ import annotations

import time
from collections import defaultdict, deque
from collections.abc import Callable
from threading import Lock

from fastapi import HTTPException, Request, status

IntProvider = int | Callable[[], int]

_rate_limit_store: dict[str, deque[float]] = defaultdict(deque)
_rate_limit_lock = Lock()


def _resolve_provider(value: IntProvider) -> int:
    return value() if callable(value) else value


def _get_client_identifier(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        forwarded_ip = forwarded_for.split(",")[0].strip()
        if forwarded_ip:
            return forwarded_ip

    if request.client and request.client.host:
        return request.client.host

    return "unknown"


def clear_rate_limit_store() -> None:
    with _rate_limit_lock:
        _rate_limit_store.clear()


def enforce_rate_limit(
    request: Request,
    *,
    bucket: str,
    max_requests: int,
    window_seconds: int,
) -> None:
    if max_requests <= 0 or window_seconds <= 0:
        return

    client_id = _get_client_identifier(request)
    key = f"{bucket}:{client_id}"
    now = time.time()
    window_start = now - window_seconds

    with _rate_limit_lock:
        timestamps = _rate_limit_store[key]
        while timestamps and timestamps[0] <= window_start:
            timestamps.popleft()

        if len(timestamps) >= max_requests:
            retry_after = max(1, int(window_seconds - (now - timestamps[0])))
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please try again later.",
                headers={"Retry-After": str(retry_after)},
            )

        timestamps.append(now)


def rate_limit_dependency(
    *,
    bucket: str,
    max_requests: IntProvider,
    window_seconds: IntProvider,
) -> Callable[[Request], None]:
    def dependency(request: Request) -> None:
        enforce_rate_limit(
            request,
            bucket=bucket,
            max_requests=_resolve_provider(max_requests),
            window_seconds=_resolve_provider(window_seconds),
        )

    return dependency
