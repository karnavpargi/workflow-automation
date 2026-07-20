"""Tests for the per-tenant rate limiter."""

from unittest.mock import MagicMock

import pytest  # noqa: F401

from ai_service.limits import RateLimiter


def _client(count: int) -> MagicMock:
    c = MagicMock()
    c.incr.return_value = count
    return c


def test_check_allows_under_limit():
    """A request under the limit returns True."""
    c = _client(count=1)
    limiter = RateLimiter(c, limit=5)
    assert limiter.check(tenant_id=1) is True


def test_check_rejects_over_limit():
    """A request over the limit returns False."""
    c = _client(count=6)
    limiter = RateLimiter(c, limit=5)
    assert limiter.check(tenant_id=1) is False


def test_check_sets_expiry_only_on_first_increment():
    """``EXPIRE`` is set only when the counter is created (count == 1)."""
    c = _client(count=1)
    limiter = RateLimiter(c, limit=5)
    limiter.check(tenant_id=42)
    c.expire.assert_called_once()
    # No further expire calls for the same minute.
    c2 = _client(count=2)
    limiter2 = RateLimiter(c2, limit=5)
    limiter2.check(tenant_id=42)
    c2.expire.assert_not_called()


def test_check_scopes_key_per_tenant_and_minute():
    """The Redis key encodes both the tenant and the minute window."""
    c = _client(count=1)
    limiter = RateLimiter(c, limit=5)
    limiter.check(tenant_id=7, now=1800.0)  # minute 30
    c.incr.assert_called_once()
    key = c.incr.call_args.args[0]
    assert key.startswith("ai_rl:tenant_7:")
    assert key.endswith(":30")
