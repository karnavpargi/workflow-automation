"""Public audit log service.

The single entry point is :func:`log`; never write ``AuditLog.objects``
calls from other apps so the append-only invariant stays in one place.
"""

from audit.models import AuditLog
from tenants.models import Tenant
from users.models import User


def log(
    *,
    tenant: Tenant,
    actor: User | None,
    event: str,
    payload: dict[str, object] | None = None,
) -> AuditLog:
    """Append an audit entry.

    Args:
        tenant: The tenant the event belongs to.
        actor: The user who performed the event (None for system actions).
        event: Dotted event name.
        payload: Optional dict of extra detail.

    Returns:
        The created AuditLog row.
    """
    return AuditLog.objects.create(
        tenant=tenant, actor=actor, event=event, payload=payload or {}
    )
