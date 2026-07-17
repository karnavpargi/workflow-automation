"""Tests for the custom User model."""

import pytest

from users.models import User


@pytest.mark.django_db
def test_create_user_email_login():
    """Users log in with email; username is separate."""
    u = User.objects.create_user(email="a@x.io", password="p", username="a")
    assert u.check_password("p") and u.email == "a@x.io"
