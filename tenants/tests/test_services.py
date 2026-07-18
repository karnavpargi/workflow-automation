"""Tests for tenant service functions."""

import pytest

from tenants import services


@pytest.mark.django_db
def test_create_tenant_adds_admin() -> None:
    """Creating a tenant also creates an ADMIN membership for the creator."""
    from users.models import User

    u = User.objects.create_user(email="o@x.io", password="p", username="o")
    t = services.create_tenant(name="Acme", slug="acme", admin=u)
    assert t.slug == "acme"
    assert t.memberships.get(user=u).role == "admin"


@pytest.mark.django_db
def test_create_tenant_slug_must_be_unique() -> None:
    """Duplicate slug raises a typed error."""
    from users.models import User

    u = User.objects.create_user(email="o@x.io", password="p", username="o")
    services.create_tenant(name="Acme", slug="acme", admin=u)
    with pytest.raises(services.TenantSlugTaken):
        services.create_tenant(name="Acme2", slug="acme", admin=u)


@pytest.mark.django_db
def test_create_tenant_writes_audit() -> None:
    from audit.models import AuditLog
    from users.models import User

    u = User.objects.create_user(email="o@x.io", password="p", username="o")
    services.create_tenant(name="Acme", slug="acme", admin=u)
    assert AuditLog.objects.filter(event="tenant.created").count() == 1
