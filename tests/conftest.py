"""Shared pytest fixtures."""

import pytest

from tenants import services
from users.models import User


@pytest.fixture
def admin_user_a():
    """Admin of tenant A."""
    u = User.objects.create_user(email="a@x.io", password="p", username="a")
    services.create_tenant(name="A", slug="a", admin=u)


@pytest.fixture
def admin_user_b():
    """Admin of tenant B."""
    u = User.objects.create_user(email="b@x.io", password="p", username="b")
    services.create_tenant(name="B", slug="b", admin=u)
