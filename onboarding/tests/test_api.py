"""Tests for the onboarding DRF API."""

import pytest
from rest_framework.test import APIClient

from tenants import services as tsvc
from users.models import User


@pytest.mark.django_db
def test_create_client_via_api():
    """POST /api/clients/ creates a client."""
    u = User.objects.create_user(email="a@x.io", password="p", username="a")
    tsvc.create_tenant(name="A", slug="a", admin=u)
    client = APIClient()
    client.force_authenticate(user=u)
    r = client.post(
        "/api/clients/",
        {"name": "Acme", "email": "a@acme.io"},
        format="json",
        HTTP_X_TENANT_SLUG="a",
    )
    assert r.status_code == 201
    assert r.data["name"] == "Acme"


@pytest.mark.django_db
def test_onboarding_status_404_for_unknown_client():
    """GET /api/clients/999/onboarding/ returns 404 for unknown id."""
    u = User.objects.create_user(email="a@x.io", password="p", username="a")
    tsvc.create_tenant(name="A", slug="a", admin=u)
    client = APIClient()
    client.force_authenticate(user=u)
    r = client.get("/api/clients/999/onboarding/", HTTP_X_TENANT_SLUG="a")
    assert r.status_code == 404
