"""Tests for the JWT login endpoints."""

import pytest
from rest_framework.test import APIClient

from tenants import services


@pytest.mark.django_db
def test_obtain_token_returns_access_and_refresh():
    """Valid email/password returns two tokens and 200."""
    from users.models import User

    u = User.objects.create_user(email="a@x.io", password="p", username="a")
    services.create_tenant(name="Acme", slug="acme", admin=u)
    client = APIClient()
    r = client.post(
        "/api/auth/token/",
        {"email": "a@x.io", "password": "p"},
        HTTP_X_TENANT_SLUG="acme",
    )
    assert r.status_code == 200
    assert "access" in r.data and "refresh" in r.data


@pytest.mark.django_db
def test_obtain_token_wrong_password_401():
    """Wrong password returns 401."""
    from users.models import User

    u = User.objects.create_user(email="a@x.io", password="p", username="a")
    services.create_tenant(name="Acme", slug="acme", admin=u)
    r = APIClient().post(
        "/api/auth/token/",
        {"email": "a@x.io", "password": "WRONG"},
        HTTP_X_TENANT_SLUG="acme",
    )
    assert r.status_code == 401
