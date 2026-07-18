"""Factory for tenant-scoped adapters."""

from integrations.base import EmailAdapter  # noqa: F401
from integrations.email.django_smtp import DjangoSmtpEmailAdapter
from integrations.models import IntegrationConfig


class AdapterNotConfigured(Exception):
    """Raised when a tenant has no active config for the requested kind."""


def get_adapter(tenant, kind: str, *, vendor: str = "minio") -> object:
    """Return an adapter instance for the tenant, kind, and vendor.

    Args:
        tenant: Tenant instance.
        kind: IntegrationConfig.Kind value.
        vendor: For kind=STORAGE, one of "minio" | "nextcloud". Default "minio".

    Returns:
        Adapter implementing the corresponding abstract interface.

    Raises:
        AdapterNotConfigured: if no active config exists or vendor unknown.
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
    if kind == IntegrationConfig.Kind.BILLING:
        from integrations.billing.invoice_ninja import InvoiceNinjaBillingAdapter

        return InvoiceNinjaBillingAdapter(cfg.credentials)
    if kind == IntegrationConfig.Kind.CRM:
        from integrations.crm.suitecrm import SuiteCrmAdapter

        return SuiteCrmAdapter(cfg.credentials)
    if kind == IntegrationConfig.Kind.STORAGE:
        if vendor == "minio":
            from integrations.storage.minio_client import MinioStorageAdapter

            return MinioStorageAdapter(cfg.credentials)
        if vendor == "nextcloud":
            from integrations.storage.nextcloud import NextcloudStorageAdapter

            return NextcloudStorageAdapter(cfg.credentials)
        raise AdapterNotConfigured(f"{kind}:{vendor}")
    raise AdapterNotConfigured(kind)
