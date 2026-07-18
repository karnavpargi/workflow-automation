"""Per-tenant integration configuration."""

from django.db import models


class IntegrationConfig(models.Model):
    """Credentials and flags for one integration kind per tenant.

    Attributes:
        tenant: Owning tenant.
        kind: One of CRM, BILLING, STORAGE, CHAT, EMAIL.
        credentials: JSON blob of vendor credentials (encrypted at rest later).
        is_active: Whether this config is currently used.
    """

    class Kind(models.TextChoices):
        """Supported integration kinds."""

        CRM = "crm", "CRM"
        BILLING = "billing", "Billing"
        STORAGE = "storage", "Storage"
        CHAT = "chat", "Chat"
        EMAIL = "email", "Email"

    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.CASCADE, related_name="integrations"
    )
    kind = models.CharField(max_length=20, choices=Kind.choices)
    credentials = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["tenant", "kind"], name="uniq_tenant_kind"),
        ]
