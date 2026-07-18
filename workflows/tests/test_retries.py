"""Tests for Celery run_handler retries and dead-letter."""

import pytest

from workflows import registry, services
from workflows.exceptions import PermanentError
from workflows.models import TaskRecord
from workflows.tasks import run_handler


@pytest.mark.django_db(transaction=True)
def test_handler_success_marks_done(settings):
    """Successful handler marks TaskRecord done."""
    settings.CELERY_TASK_ALWAYS_EAGER = True
    from tenants import services as tsvc
    from users.models import User

    def handler(event):
        return "ok"

    registry.register("ok.event", handler)
    u = User.objects.create_user(email="a@x.io", password="p", username="a")
    t = tsvc.create_tenant(name="A", slug="a", admin=u)
    e = services.emit_event(
        tenant=t,
        name="ok.event",
        payload={},
        task_name="ok",
        entity_id="1",
        step="s",
    )
    tr = TaskRecord.objects.get(event=e)
    run_handler(tr.id)
    tr.refresh_from_db()
    assert tr.status == TaskRecord.Status.DONE


@pytest.mark.django_db(transaction=True)
def test_permanent_error_marks_dead(settings):
    """PermanentError marks task dead without retry."""
    settings.CELERY_TASK_ALWAYS_EAGER = True
    from tenants import services as tsvc
    from users.models import User

    def handler(event):
        raise PermanentError("nope")

    registry.register("bad.event", handler)
    u = User.objects.create_user(email="a@x.io", password="p", username="a")
    t = tsvc.create_tenant(name="A", slug="a", admin=u)
    e = services.emit_event(
        tenant=t,
        name="bad.event",
        payload={},
        task_name="bad",
        entity_id="1",
        step="s",
    )
    tr = TaskRecord.objects.get(event=e)
    run_handler(tr.id)
    tr.refresh_from_db()
    assert tr.status == TaskRecord.Status.DEAD
