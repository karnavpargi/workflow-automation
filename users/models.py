"""Custom user model for the platform.

Roles are stored on ``Membership`` (tenants app) so a single user can hold
different roles across tenants.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """User account; email is the unique login identifier.

    Attributes:
        email: Unique login email.
        username: Kept for Django admin compatibility.
    """

    email = models.EmailField(unique=True)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self) -> str:
        """Return the user's email."""
        return self.email
