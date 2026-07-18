"""Tests for role-based DRF permission classes."""

from typing import Any

import pytest
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from tenants import services
from users.models import User
from users.permissions import IsTenantAdmin, IsTenantMember


def _req(user: User) -> Request:
    r = APIRequestFactory().get("/")
    r.user = user
    return r


@pytest.mark.django_db
def test_is_tenant_admin_true_for_admin_member() -> None:
    u = User.objects.create_user(email="o@x.io", password="p", username="o")
    t = services.create_tenant(name="Acme", slug="acme", admin=u)
    r: Any = _req(u)
    r.tenant = t
    assert IsTenantAdmin().has_permission(r, None) is True  # type: ignore[arg-type]


@pytest.mark.django_db
def test_is_tenant_member_false_for_outsider() -> None:
    member = User.objects.create_user(email="m@x.io", password="p", username="m")
    outsider = User.objects.create_user(email="z@x.io", password="p", username="z")
    t = services.create_tenant(name="Acme", slug="acme", admin=member)
    r: Any = _req(outsider)
    r.tenant = t
    assert IsTenantMember().has_permission(r, None) is False  # type: ignore[arg-type]
