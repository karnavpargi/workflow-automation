"""Tenant and Membership models.

A tenant is an agency; every tenant-scoped row in the system carries
``tenant_id`` and is protected by a Row-Level Security policy (Task 7).
Memberships link users to tenants with a role.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _


class Tenant(models.Model):
    """An agency tenant.

    Attributes:
        name: Human-readable agency name.
        slug: URL-safe identifier used in subdomains / path prefixes.
        created_at: UTC timestamp of creation.
        is_active: Soft-disable flag for suspended tenants.
    """

    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        """Return the tenant name."""
        return self.name


class Membership(models.Model):
    """Links a user to a tenant with a role.

    Attributes:
        tenant: The tenant the user belongs to.
        user: The user (custom User model).
        role: One of ADMIN, MEMBER, CLIENT.
    """

    class Role(models.TextChoices):
        """RBAC roles used throughout the platform."""

        ADMIN = "admin", _("Admin")
        MEMBER = "member", _("Member")
        CLIENT = "client", _("Client")

    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="memberships"
    )
    user = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="memberships"
    )
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.MEMBER)

    class Meta:
        """Membership model metadata."""

        constraints = [
            models.UniqueConstraint(fields=["tenant", "user"], name="uniq_tenant_user"),
        ]

    def __str__(self) -> str:
        """Return user@slug for debugging."""
        return f"{self.user.email}@{self.tenant.slug}"
