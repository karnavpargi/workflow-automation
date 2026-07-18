"""Tests for adapter base interfaces."""

from integrations.base import (
    BillingAdapter,  # noqa: F401
    ChatAdapter,  # noqa: F401
    CrmAdapter,
    EmailAdapter,  # noqa: F401
    IntegrationAuthFailed,
    IntegrationRateLimited,
    IntegrationUnavailable,
    StorageAdapter,  # noqa: F401
)


def test_exceptions_are_distinct():
    """Typed exceptions exist and are independent classes."""
    assert issubclass(IntegrationUnavailable, Exception)
    assert IntegrationAuthFailed is not IntegrationRateLimited


def test_abstract_adapters_require_methods():
    """Abstract methods raise TypeError if not implemented."""
    import pytest

    with pytest.raises(TypeError):
        CrmAdapter()  # type: ignore[abstract]
