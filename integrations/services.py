"""Factory for tenant-scoped adapters."""

from integrations.base import EmailAdapter  # noqa: F401
from integrations.email.django_smtp import DjangoSmtpEmailAdapter
from integrations.models import IntegrationConfig


class AdapterNotConfigured(Exception):
    """Raised when a tenant has no active config for the requested kind."""


def get_adapter(tenant, kind: str):
    """Return an adapter instance for the tenant and kind.

    Args:
        tenant: Tenant instance.
        kind: IntegrationConfig.Kind value.

    Returns:
        Adapter implementing the corresponding abstract interface.

    Raises:
        AdapterNotConfigured: if no active config exists.
    """
    try:
        cfg = IntegrationConfig.objects.get(tenant=tenant, kind=kind, is_active=True)
    except IntegrationConfig.DoesNotExist as exc:
        raise AdapterNotConfigured(kind) from exc
    if kind == IntegrationConfig.Kind.EMAIL:
        return DjangoSmtpEmailAdapter(cfg.credentials)
    if kind == IntegrationConfig.Kind.CHAT:
        from integrations.chat.mattermost import MattermostChatAdapter

        return MattermostChatAdapter(cfg.credentials)
    if kind == IntegrationConfig.Kind.STORAGE:
        from integrations.storage.minio_client import MinioStorageAdapter

        return MinioStorageAdapter(cfg.credentials)
    if kind == IntegrationConfig.Kind.BILLING:
        from integrations.billing.invoice_ninja import InvoiceNinjaBillingAdapter

        return InvoiceNinjaBillingAdapter(cfg.credentials)
    raise AdapterNotConfigured(kind)
