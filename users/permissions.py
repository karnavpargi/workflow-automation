"""DRF permission classes that combine auth with tenant membership."""

from typing import Any, cast

from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from tenants.models import Tenant
from users.models import User


class _TenantPermission(BasePermission):
    """Base class requiring a resolved ``request.tenant``."""

    def has_permission(self, request: Request, view: APIView) -> bool:
        """Reject if there is no tenant on the request.

        Args:
            request: DRF request with ``tenant`` attached by middleware.
            view: The view being accessed.

        Returns:
            True if a tenant is present and the role check passes.
        """
        tenant = cast(Tenant | None, getattr(request, "tenant", None))
        if tenant is None or not request.user.is_authenticated:
            return False
        return self.role_check(request, tenant)

    def role_check(self, request: Request, tenant: Tenant) -> bool:
        """Override in subclasses; default denies everyone."""
        return False


class IsTenantMember(_TenantPermission):
    """Allow any user with a membership on the current tenant."""

    def role_check(self, request: Request, tenant: Tenant) -> bool:
        """Return True if the user has any membership on the tenant.

        Args:
            request: DRF request.
            tenant: The resolved Tenant.

        Returns:
            True when a membership exists for the user on this tenant.
        """
        user = cast(User, request.user)
        return tenant.memberships.filter(user=user).exists()


class IsTenantAdmin(IsTenantMember):
    """Allow only users with the ADMIN role on the current tenant."""

    def role_check(self, request: Request, tenant: Tenant) -> bool:
        """Return True only if the user is an ADMIN of the tenant.

        Args:
            request: DRF request.
            tenant: The resolved Tenant.

        Returns:
            True when an ADMIN membership exists.
        """
        from tenants.models import Membership

        user = cast(User, request.user)
        return tenant.memberships.filter(user=user, role=Membership.Role.ADMIN).exists()


class IsClient(BasePermission):
    """Allow authenticated users (clients access the client portal by token)."""

    def has_permission(self, request: Request, view: APIView) -> bool:
        """Return True when the request user is authenticated.

        Args:
            request: DRF request.
            view: The view being accessed.

        Returns:
            True for any authenticated user; client-level scoping is the
            view's responsibility.
        """
        user: Any = request.user
        return bool(user and user.is_authenticated)
