"""Tests for Event and TaskRecord models."""

import pytest

from workflows.models import Event, TaskRecord


@pytest.mark.django_db
def test_event_create():
    """Event stores name, tenant, payload, created_at."""
    from tenants import services
    from users.models import User

    u = User.objects.create_user(email="a@x.io", password="p", username="a")
    t = services.create_tenant(name="A", slug="a", admin=u)
    e = Event.objects.create(tenant=t, name="client.created", payload={"id": 1})
    assert e.name == "client.created" and e.payload == {"id": 1}


@pytest.mark.django_db
def test_task_record_status_defaults_pending():
    """New TaskRecord starts as pending."""
    from tenants import services
    from users.models import User

    u = User.objects.create_user(email="a@x.io", password="p", username="a")
    t = services.create_tenant(name="A", slug="a", admin=u)
    e = Event.objects.create(tenant=t, name="x", payload={})
    tr = TaskRecord.objects.create(
        tenant=t,
        event=e,
        task_name="onboarding.start",
        idempotency_key="onboarding.start:1:step1",
    )
    assert tr.status == TaskRecord.Status.PENDING
