"""Follow-up services.

Three public functions:
  * :func:`schedule_invoice_reminder` is the Plan 5 hook called by
    :func:`invoices.services.issue_invoice`. It creates a PENDING
    :class:`~followups.models.Reminder` 7 days before the invoice due
    date.
  * :func:`process_due_reminders` is the Celery Beat entry point. It
    scans all due PENDING reminders, sends them through the active
    :class:`~integrations.base.EmailAdapter`, marks them SENT, and
    appends a ``followup.sent`` audit entry.
  * :func:`create_draft_reminder` is the Plan 9 HITL hook called by
    the AI service's FollowupDraftingAgent. It stores an LLM-proposed
    message in ``DRAFT`` status for human review.
  * :func:`approve_draft` flips a DRAFT reminder back to PENDING so it
    flows through the normal send path.
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


def create_draft_reminder(
    *,
    tenant,
    subject: str,
    recipient_email: str,
    invoice_number: str,
    due_date_iso: str,
    draft_text: str,
    due_at=None,
) -> Reminder:
    """Persist an LLM-drafted reminder in ``DRAFT`` status.

    Args:
        tenant: Owning tenant.
        subject: Reminder subject.
        recipient_email: Recipient address.
        invoice_number: Invoice reference for context.
        due_date_iso: ISO date string for context.
        draft_text: The LLM-proposed message body.
        due_at: Optional explicit due datetime. Defaults to ``now``.

    Returns:
        Created :class:`Reminder` in ``DRAFT`` status.
    """
    return Reminder.objects.create(
        tenant=tenant,
        subject=subject,
        due_at=due_at or timezone.now(),
        recipient_email=recipient_email,
        status=Reminder.Status.DRAFT,
        draft_text=draft_text,
        context={
            "subject": subject,
            "due_date": due_date_iso,
            "number": invoice_number,
        },
    )


def approve_draft(reminder: Reminder) -> Reminder:
    """Flip a ``DRAFT`` reminder to ``PENDING`` for the send path.

    Args:
        reminder: Reminder in ``DRAFT`` status.

    Returns:
        The updated reminder.
    """
    if reminder.status != Reminder.Status.DRAFT:
        return reminder
    reminder.status = Reminder.Status.PENDING
    reminder.save(update_fields=["status"])
    return reminder


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
                else rem.draft_text or f"Reminder: {rem.subject}"
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
