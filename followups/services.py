"""Follow-up services.

Two public functions:
  * :func:`schedule_invoice_reminder` is the Plan 5 hook called by
    :func:`invoices.services.issue_invoice`. It creates a PENDING
    :class:`~followups.models.Reminder` 7 days before the invoice due
    date.
  * :func:`process_due_reminders` is the Celery Beat entry point. It
    scans all due PENDING reminders, sends them through the active
    :class:`~integrations.base.EmailAdapter`, marks them SENT, and
    appends a ``followup.sent`` audit entry.
"""

from datetime import datetime, timedelta

from django.utils import timezone

from audit.services import log as audit_log
from followups.models import Reminder
from integrations.models import IntegrationConfig
from integrations.services import get_adapter


def schedule_invoice_reminder(invoice) -> object:
    """Schedule a reminder 7 days before the invoice due date.

    Args:
        invoice: Issued :class:`invoices.models.Invoice`.

    Returns:
        Created :class:`~followups.models.Reminder`.
    """
    due_at = timezone.make_aware(
        datetime.combine(invoice.due_date - timedelta(days=7), datetime.min.time())
    )
    return Reminder.objects.create(
        tenant=invoice.tenant,
        subject=f"Invoice {invoice.number} due",
        due_at=due_at,
        recipient_email=invoice.client.email,
        context={
            "subject": f"Invoice {invoice.number}",
            "due_date": invoice.due_date.isoformat(),
            "number": invoice.number,
        },
    )


def process_due_reminders() -> int:
    """Send every PENDING reminder whose ``due_at`` has passed.

    For each reminder, the rule template (if any) is filled from the
    stored context and dispatched through the tenant's active
    :class:`~integrations.base.EmailAdapter`. The reminder is then
    flipped to SENT and a ``followup.sent`` audit entry is appended.

    Returns:
        Number of reminders processed.
    """
    now = timezone.now()
    qs = Reminder.objects.filter(status=Reminder.Status.PENDING, due_at__lte=now)
    count = 0
    for rem in qs.select_related("tenant", "rule"):
        if rem.recipient_email:
            body = (
                rem.rule.template.format(**rem.context)
                if rem.rule
                else f"Reminder: {rem.subject}"
            )
            email = get_adapter(rem.tenant, IntegrationConfig.Kind.EMAIL)
            email.send(
                to=[rem.recipient_email],
                subject=rem.subject,
                body=body,
            )
        rem.status = Reminder.Status.SENT
        rem.save(update_fields=["status"])
        audit_log(
            tenant=rem.tenant,
            actor=None,
            event="followup.sent",
            payload={"reminder_id": rem.id},
        )
        count += 1
    return count
