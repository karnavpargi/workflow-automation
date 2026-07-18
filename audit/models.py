"""Append-only audit log model.

Every meaningful state change in the platform writes one row here via
:func:`audit.services.log`. The table is declared append-only at the DB
level by a trigger added in the migration (block UPDATE/DELETE).
"""

from django.db import models


class AuditLog(models.Model):
    """Immutable record of a tenant-scoped event.

    Attributes:
        tenant: The tenant within which the event occurred.
        actor: The user who triggered the event (nullable for system events).
        event: A dotted event name (e.g. ``tenant.created``).
        payload: Arbitrary JSON detail about the event.
        created_at: UTC timestamp.
    """

    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.CASCADE, related_name="audit_logs"
    )
    actor = models.ForeignKey(
        "users.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_logs",
    )
    event = models.CharField(max_length=100)
    payload = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """AuditLog model metadata."""

        indexes = [models.Index(fields=["tenant", "event"])]
