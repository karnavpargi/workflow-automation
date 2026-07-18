"""Tests for IntegrationConfig and get_adapter."""

import pytest

from integrations.base import EmailAdapter
from integrations.models import IntegrationConfig
from integrations.services import get_adapter


@pytest.mark.django_db
def test_get_adapter_email_returns_smtp():
    """Configured email adapter returns EmailAdapter implementation."""
    from tenants import services
    from users.models import User

    u = User.objects.create_user(email="a@x.io", password="p", username="a")
    t = services.create_tenant(name="A", slug="a", admin=u)
    IntegrationConfig.objects.create(
        tenant=t,
        kind=IntegrationConfig.Kind.EMAIL,
        credentials={"backend": "smtp"},
        is_active=True,
    )
    adapter = get_adapter(t, IntegrationConfig.Kind.EMAIL)
    assert isinstance(adapter, EmailAdapter)


@pytest.mark.django_db
def test_get_adapter_storage_nextcloud():
    """STORAGE + vendor='nextcloud' returns NextcloudStorageAdapter."""
    from integrations.storage.nextcloud import NextcloudStorageAdapter
    from tenants import services
    from users.models import User

    u = User.objects.create_user(email="a@x.io", password="p", username="a")
    t = services.create_tenant(name="A", slug="a", admin=u)
    IntegrationConfig.objects.create(
        tenant=t,
        kind=IntegrationConfig.Kind.STORAGE,
        credentials={
            "base_url": "https://nc.example.com",
            "username": "u",
            "password": "p",
        },
        is_active=True,
        vendor="nextcloud",
    )
    adapter = get_adapter(t, IntegrationConfig.Kind.STORAGE, vendor="nextcloud")
    assert isinstance(adapter, NextcloudStorageAdapter)
