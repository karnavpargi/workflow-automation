"""Celery tasks for the invoicing app."""

import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from invoices.models import RecurringSchedule
from invoices.services import issue_invoice_from_schedule

logger = logging.getLogger(__name__)


@shared_task
def check_recurring_invoices() -> int:
    """Issue invoices for due recurring schedules; advance next_run.

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
            logger.exception(
                "Failed to issue invoice for schedule %s: %s", sched.id, exc
            )
        # Advance next_run regardless of success (avoid infinite retries)
        if sched.cadence == "monthly":
            sched.next_run = today + timedelta(days=30)
        elif sched.cadence == "weekly":
            sched.next_run = today + timedelta(days=7)
        sched.save(update_fields=["next_run"])
    return count
