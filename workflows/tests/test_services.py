"""Tests for workflow services."""

import pytest

from workflows import registry, services
from workflows.models import TaskRecord


@pytest.mark.django_db(transaction=True)
def test_emit_event_creates_row_and_enqueues():
    """emit_event persists Event and creates TaskRecord when handler exists."""
    from tenants import services as tsvc
    from users.models import User

    def handler(event):  # noqa: ANN001
        return None

    registry.register("client.created", handler)
    u = User.objects.create_user(email="a@x.io", password="p", username="a")
    t = tsvc.create_tenant(name="A", slug="a", admin=u)
    e = services.emit_event(
        tenant=t,
        name="client.created",
        payload={"id": 1},
        task_name="onboarding.start",
        entity_id="1",
        step="start",
    )
    assert e.name == "client.created"
    assert TaskRecord.objects.filter(event=e).count() == 1


@pytest.mark.django_db(transaction=True)
def test_enqueue_is_idempotent():
    """Second enqueue with same key is a no-op."""
    from tenants import services as tsvc
    from users.models import User

    def handler(event):  # noqa: ANN001
        return None

    registry.register("x", handler)
    u = User.objects.create_user(email="a@x.io", password="p", username="a")
    t = tsvc.create_tenant(name="A", slug="a", admin=u)
    e = services.emit_event(
        tenant=t,
        name="x",
        payload={},
        task_name="t",
        entity_id="1",
        step="s",
    )
    tr1 = TaskRecord.objects.get(event=e)
    tr2 = services.enqueue_task(
        tenant=t,
        event=e,
        task_name="t",
        entity_id="1",
        step="s",
    )
    assert tr1.id == tr2.id
    assert TaskRecord.objects.count() == 1
