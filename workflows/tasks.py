"""Celery tasks for the workflows engine.

This is a stub from Task 3. The real implementation is added in Task 4.
"""

from celery import shared_task


@shared_task
def run_handler(task_record_id: int) -> None:
    """No-op placeholder; replaced in Task 4."""
    return None
