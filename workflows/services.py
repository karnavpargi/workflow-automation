"""Public workflow services: emit events and enqueue tasks."""

from django.db import transaction

from workflows.models import Event, TaskRecord


def make_idempotency_key(task_name: str, entity_id: str, step: str) -> str:
    """Build a stable idempotency key.

    Args:
        task_name: Celery task name.
        entity_id: Target entity primary key as string.
        step: Logical step name within the workflow.

    Returns:
        Unique key string.
    """
    return f"{task_name}:{entity_id}:{step}"


def emit_event(
    *,
    tenant,
    name: str,
    payload: dict,
    task_name: str,
    entity_id: str,
    step: str,
) -> Event:
    """Persist an Event and enqueue its handler task after commit.

    Args:
        tenant: Owning tenant.
        name: Event name.
        payload: Event body.
        task_name: Celery task to run.
        entity_id: Entity id for the idempotency key.
        step: Step name for the idempotency key.

    Returns:
        The created Event.
    """
    e = Event.objects.create(tenant=tenant, name=name, payload=payload)
    transaction.on_commit(
        lambda: enqueue_task(
            tenant=tenant,
            event=e,
            task_name=task_name,
            entity_id=entity_id,
            step=step,
        )
    )
    return e


def enqueue_task(
    *,
    tenant,
    event: Event,
    task_name: str,
    entity_id: str,
    step: str,
) -> TaskRecord:
    """Create or return existing TaskRecord; dispatch Celery if new.

    Args:
        tenant: Owning tenant.
        event: Parent Event.
        task_name: Celery task name.
        entity_id: Entity id for the key.
        step: Step name for the key.

    Returns:
        Existing or newly created TaskRecord.
    """
    key = make_idempotency_key(task_name, entity_id, step)
    tr, created = TaskRecord.objects.get_or_create(
        idempotency_key=key,
        defaults={
            "tenant": tenant,
            "event": event,
            "task_name": task_name,
            "status": TaskRecord.Status.PENDING,
        },
    )
    if created:
        from workflows.tasks import run_handler

        run_handler.delay(tr.id)
    return tr


def mark_running(tr: TaskRecord) -> None:
    """Mark a task as running and bump attempts.

    Args:
        tr: TaskRecord to update.
    """
    tr.status = TaskRecord.Status.RUNNING
    tr.attempts += 1
    tr.save(update_fields=["status", "attempts", "updated_at"])


def mark_done(tr: TaskRecord) -> None:
    """Mark a task as done.

    Args:
        tr: TaskRecord to update.
    """
    tr.status = TaskRecord.Status.DONE
    tr.save(update_fields=["status", "updated_at"])


def mark_failed(tr: TaskRecord, error: str) -> None:
    """Mark a task as failed with an error message.

    Args:
        tr: TaskRecord to update.
        error: Error message.
    """
    tr.status = TaskRecord.Status.FAILED
    tr.last_error = error
    tr.save(update_fields=["status", "last_error", "updated_at"])


def mark_dead(tr: TaskRecord, error: str) -> None:
    """Mark a task as dead after retries exhausted.

    Args:
        tr: TaskRecord to update.
        error: Final error message.
    """
    tr.status = TaskRecord.Status.DEAD
    tr.last_error = error
    tr.save(update_fields=["status", "last_error", "updated_at"])
