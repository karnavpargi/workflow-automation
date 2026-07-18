"""Onboarding services."""

from django.db import transaction

from audit.services import log as audit_log
from onboarding.models import Client
from workflows import services as wsvc


def create_client(*, tenant, name: str, email: str) -> Client:
    """Create a client and emit client.created.

    Args:
        tenant: Owning tenant.
        name: Client name.
        email: Contact email.

    Returns:
        The created Client.
    """
    with transaction.atomic():
        client = Client.objects.create(tenant=tenant, name=name, email=email)
        wsvc.emit_event(
            tenant=tenant,
            name="client.created",
            payload={"client_id": client.id, "email": email, "name": name},
            task_name="onboarding.start",
            entity_id=str(client.id),
            step="start",
        )
        audit_log(
            tenant=tenant,
            actor=None,
            event="client.created",
            payload={"client_id": client.id},
        )
    return client
