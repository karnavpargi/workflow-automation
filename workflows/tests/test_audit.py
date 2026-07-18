"""Tests for the audit hook on dead tasks."""

import pytest

from workflows import registry, services
from workflows.exceptions import PermanentError
from workflows.models import TaskRecord
from workflows.tasks import run_handler


@pytest.mark.django_db(transaction=True)
def test_mark_dead_writes_audit_event(settings):
    """When a task dies, an audit row is written with the right payload."""
    settings.CELERY_TASK_ALWAYS_EAGER = True
    from audit.models import AuditLog
    from tenants import services as tsvc
    from users.models import User

    def handler(event):
        raise PermanentError("boom")

    registry.register("audit.dead", handler)
    u = User.objects.create_user(email="a@x.io", password="p", username="a")
    t = tsvc.create_tenant(name="A", slug="a", admin=u)
    e = services.emit_event(
        tenant=t,
        name="audit.dead",
        payload={},
        task_name="t",
        entity_id="1",
        step="s",
    )
    tr = TaskRecord.objects.get(event=e)
    before = AuditLog.objects.filter(tenant=t, event="workflow.task.dead").count()
    run_handler(tr.id)
    tr.refresh_from_db()
    after = AuditLog.objects.filter(tenant=t, event="workflow.task.dead").count()

    assert tr.status == TaskRecord.Status.DEAD
    assert after == before + 1
    row = AuditLog.objects.filter(tenant=t, event="workflow.task.dead").latest("id")
    assert row.payload["task_record_id"] == tr.id
    assert row.payload["task_name"] == "t"
    assert row.payload["error"] == "boom"
    assert row.actor is None
