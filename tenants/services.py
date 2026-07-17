"""Public service interface for tenant operations.

Other apps MUST go through this module, never touch ``Tenant.objects``
directly, so multi-tenancy invariants stay in one place.
"""

from django.db import transaction

from tenants.models import Membership, Tenant


class TenantSlugTaken(Exception):
    """Raised when creating a tenant with a slug already in use."""


def create_tenant(*, name: str, slug: str, admin) -> Tenant:
    """Create a tenant and add ``admin`` as its first ADMIN member.

    Args:
        name: Human-readable tenant name.
        slug: Unique URL-safe slug.
        admin: User instance to make the first admin.

    Returns:
        The created Tenant.

    Raises:
        TenantSlugTaken: if slug is already used.
    """
    if Tenant.objects.filter(slug=slug).exists():
        raise TenantSlugTaken(slug)
    with transaction.atomic():
        t = Tenant.objects.create(name=name, slug=slug)
        Membership.objects.create(tenant=t, user=admin, role=Membership.Role.ADMIN)
        from audit.services import log as audit_log

        audit_log(tenant=t, actor=admin, event="tenant.created", payload={"slug": slug})
    return t
