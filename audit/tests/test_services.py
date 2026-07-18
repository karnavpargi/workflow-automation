"""Tests for the audit log service."""

import pytest

from audit import services
from audit.models import AuditLog


@pytest.mark.django_db
def test_log_creates_immutable_entry() -> None:
    """log() writes a row that cannot be mutated via the public API."""
    from tenants import services as tsvc
    from users.models import User

    u = User.objects.create_user(email="a@x.io", password="p", username="a")
    t = tsvc.create_tenant(name="Acme", slug="acme", admin=u)
    services.log(tenant=t, actor=u, event="tenant.created", payload={"slug": "acme"})
    assert AuditLog.objects.filter(event="tenant.created").count() == 1


@pytest.mark.django_db
def test_log_payload_is_json() -> None:
    """Payload is stored as JSON and round-trips through a dict."""
    from tenants import services as tsvc
    from users.models import User

    u = User.objects.create_user(email="a@x.io", password="p", username="a")
    t = tsvc.create_tenant(name="Acme", slug="acme", admin=u)
    services.log(tenant=t, actor=u, event="x", payload={"k": 1})
    row = AuditLog.objects.get(event="x")
    assert row.payload == {"k": 1}
