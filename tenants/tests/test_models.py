"""Tests for Tenant and Membership models."""

import pytest

from tenants.models import Membership, Tenant
from users.models import User


@pytest.mark.django_db
def test_tenant_create_has_defaults():
    """Creating a tenant fills name, slug, created_at."""
    t = Tenant.objects.create(name="Acme", slug="acme")
    assert t.id and t.name == "Acme" and t.slug == "acme"
    assert t.created_at is not None


@pytest.mark.django_db
def test_membership_str_and_role():
    """Membership links a user to a tenant with a role."""
    t = Tenant.objects.create(name="Acme", slug="acme")
    u = User.objects.create_user(email="a@acme.io", password="x")
    m = Membership.objects.create(tenant=t, user=u, role=Membership.Role.ADMIN)
    assert m.role == Membership.Role.ADMIN
    assert str(m) == "a@acme.io@acme"
