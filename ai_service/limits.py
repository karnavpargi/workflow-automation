"""Per-tenant rate limits for the AI service (Redis-backed).

Fixed-window counter: each request increments a Redis key scoped to
``(tenant_id, minute)``; when the count exceeds the configured limit,
the request is rejected with 429. Cheap to implement, predictable for
operators, and good enough for an MVP. A future task can swap in a
sliding-window or token-bucket implementation without changing the
public API.

The Redis URL is read from ``AI_REDIS_URL`` (env: ``AI_REDIS_URL``,
default ``redis://localhost:6379/2``); tests inject a stub client.
"""

import os
import time
from collections.abc import Callable

DEFAULT_LIMIT_PER_MINUTE = 60


def _redis_url() -> str:
    """Return the configured Redis URL."""
    return os.environ.get("AI_REDIS_URL", "redis://localhost:6379/2")


def _key(tenant_id: int, window: int) -> str:
    """Build the Redis key for a (tenant, window) bucket."""
    return f"ai_rl:tenant_{tenant_id}:{window}"


class RateLimiter:
    """Fixed-window per-tenant rate limiter.

    Args:
        client: A ``redis.Redis``-compatible client. Tests inject a stub.
        limit: Maximum requests per minute per tenant.
    """

    def __init__(self, client, *, limit: int = DEFAULT_LIMIT_PER_MINUTE) -> None:
        self._client = client
        self._limit = limit

    def check(self, tenant_id: int, *, now: float | None = None) -> bool:
        """Return True if ``tenant_id`` is under the limit for the current minute.

        Args:
            tenant_id: The tenant to check.
            now: Optional override of ``time.time`` (used in tests).

        Returns:
            True when the request is allowed, False when over limit.
        """
        current_minute = int((now if now is not None else time.time()) // 60)
        key = _key(tenant_id, current_minute)
        count = self._client.incr(key)
        if count == 1:
            self._client.expire(key, 65)  # slight overlap
        return count <= self._limit


def build_default_limiter(client_factory: Callable | None = None):
    """Return a default ``RateLimiter`` using the configured Redis URL.

    Args:
        client_factory: Optional callable returning a Redis-compatible
            client. Defaults to ``redis.Redis.from_url(_redis_url())``.

    Returns:
        A :class:`RateLimiter` instance.
    """
    if client_factory is None:
        import redis

        client = redis.Redis.from_url(_redis_url())
    else:
        client = client_factory()
    return RateLimiter(client)
