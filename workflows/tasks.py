"""Celery tasks for the workflow engine."""

from celery import shared_task

from workflows import registry, services
from workflows.exceptions import PermanentError
from workflows.models import TaskRecord

MAX_RETRIES = 3
BACKOFF = {0: 60, 1: 300, 2: 1800}  # seconds


@shared_task(bind=True, max_retries=MAX_RETRIES)
def run_handler(self, task_record_id: int) -> None:
    """Execute the registered handler for a TaskRecord.

    Args:
        self: Bound Celery task.
        task_record_id: PK of the TaskRecord to run.

    Raises:
        RetryableError: re-raised after scheduling a retry.
    """
    tr = TaskRecord.objects.select_related("event", "tenant").get(pk=task_record_id)
    if tr.status == TaskRecord.Status.DONE:
        return
    services.mark_running(tr)
    try:
        handler = registry.get(tr.event.name)
        handler(tr.event)
        services.mark_done(tr)
    except PermanentError as exc:
        services.mark_dead(tr, str(exc))
    except Exception as exc:  # noqa: BLE001
        if tr.attempts >= MAX_RETRIES:
            services.mark_dead(tr, str(exc))
            return
        services.mark_failed(tr, str(exc))
        countdown = BACKOFF.get(tr.attempts - 1, 1800)
        raise self.retry(exc=exc, countdown=countdown) from exc
