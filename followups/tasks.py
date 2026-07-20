"""Celery tasks for the followups app.

The reminder processor runs on an hourly Beat schedule and delegates to
:func:`followups.services.process_due_reminders`. Kept as a thin
wrapper so the Beat entry point is greppable and the service remains
trivially unit-testable without Celery machinery.
"""

from celery import shared_task

from followups.services import process_due_reminders


@shared_task
def process_due_reminders_task() -> int:
    """Send all due PENDING reminders via the active EmailAdapter.

    Returns:
        Number of reminders processed.
    """
    return process_due_reminders()
