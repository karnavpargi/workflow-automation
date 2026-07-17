"""Tests for role-based DRF permission classes."""

import pytest
from rest_framework.test import APIRequestFactory

from tenants import services
from users.permissions import IsTenantAdmin, IsTenantMember


def _req(user):
    r = APIRequestFactory().get("/")
    r.user = user
    return r


@pytest.mark.django_db
def test_is_tenant_admin_true_for_admin_member():
    from users.models import User

    u = User.objects.create_user(email="o@x.io", password="p", username="o")
    t = services.create_tenant(name="Acme", slug="acme", admin=u)
    r = _req(u)
    r.tenant = t
    assert IsTenantAdmin().has_permission(r, None) is True


@pytest.mark.django_db
def test_is_tenant_member_false_for_outsider():
    from users.models import User

    member = User.objects.create_user(email="m@x.io", password="p", username="m")
    outsider = User.objects.create_user(email="z@x.io", password="p", username="z")
    t = services.create_tenant(name="Acme", slug="acme", admin=member)
    r = _req(outsider)
    r.tenant = t
    assert IsTenantMember().has_permission(r, None) is False
