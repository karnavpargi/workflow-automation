"""Celery tasks for the invoicing app."""

import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from invoices.models import RecurringSchedule
from invoices.services import issue_invoice_from_schedule

logger = logging.getLogger(__name__)

MAX_CONSECUTIVE_FAILURES = 3


@shared_task
def check_recurring_invoices() -> int:
    """Issue invoices for due recurring schedules; advance next_run.

    On failure, increment ``consecutive_failures``; after
    ``MAX_CONSECUTIVE_FAILURES`` failures in a row, disable the schedule
    and emit a critical log. On success, reset the counter.

    Returns:
        Number of invoices issued.
    """
    today = timezone.now().date()
    due = RecurringSchedule.objects.filter(is_active=True, next_run__lte=today)
    count = 0
    for sched in due.select_related("tenant", "client"):
        try:
            issue_invoice_from_schedule(sched)
            count += 1
        except Exception as exc:  # noqa: BLE001
            sched.consecutive_failures += 1
            if sched.consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                sched.is_active = False
                logger.critical(
                    "Recurring schedule %s disabled after %d consecutive failures",
                    sched.id,
                    sched.consecutive_failures,
                )
            else:
                logger.exception(
                    "Failed to issue invoice for schedule %s: %s", sched.id, exc
                )
        else:
            sched.consecutive_failures = 0
        # Advance next_run regardless of success (avoid infinite retries)
        if sched.cadence == "monthly":
            sched.next_run = today + timedelta(days=30)
        elif sched.cadence == "weekly":
            sched.next_run = today + timedelta(days=7)
        sched.save(update_fields=["next_run", "consecutive_failures", "is_active"])
    return count
