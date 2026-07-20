# ruff: noqa: I001, F401
"""Tests for schedule_invoice_reminder and process_due_reminders services."""

from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.django_db
def test_schedule_invoice_reminder_creates_pending_reminder_seven_days_before_due():
    """schedule_invoice_reminder creates a PENDING reminder 7 days before due_date."""
    from followups.models import Reminder
    from followups.services import schedule_invoice_reminder
    from invoices.models import Invoice
    from onboarding.models import Client
    from tenants import services as tsvc
    from users.models import User

    u = User.objects.create_user(email="a@x.io", password="p", username="a")
    t = tsvc.create_tenant(name="A", slug="a", admin=u)
    c = Client.objects.create(tenant=t, name="Acme", email="a@acme.io")
    inv = Invoice.objects.create(
        tenant=t, client=c, number="INV-1", due_date=date(2026, 12, 31)
    )

    rem = schedule_invoice_reminder(inv)

    assert rem is not None
    assert rem.status == Reminder.Status.PENDING
    assert rem.recipient_email == "a@acme.io"
    assert rem.tenant_id == t.id
    # 7 days before due date at 00:00 UTC
    assert rem.due_at.date() == date(2026, 12, 24)
    assert rem.subject == "Invoice INV-1 due"
    assert rem.context["subject"] == "Invoice INV-1"
    assert rem.context["due_date"] == "2026-12-31"


@pytest.mark.django_db
def test_process_due_reminders_sends_email_marks_sent_and_audits():
    """process_due_reminders sends email, marks SENT, writes audit entry."""
    from followups.models import Reminder
    from followups.services import process_due_reminders, schedule_invoice_reminder
    from integrations.models import IntegrationConfig
    from invoices.models import Invoice
    from onboarding.models import Client
    from tenants import services as tsvc
    from users.models import User

    u = User.objects.create_user(email="a@x.io", password="p", username="a")
    t = tsvc.create_tenant(name="A", slug="a", admin=u)
    c = Client.objects.create(tenant=t, name="Acme", email="a@acme.io")
    inv = Invoice.objects.create(
        tenant=t, client=c, number="INV-1", due_date=date(2026, 1, 1)
    )
    IntegrationConfig.objects.create(
        tenant=t,
        kind=IntegrationConfig.Kind.EMAIL,
        is_active=True,
        credentials={"backend": "smtp"},
    )
    rem = schedule_invoice_reminder(inv)
    # Backdate the reminder so it's due now
    from django.utils import timezone

    Reminder.objects.filter(pk=rem.pk).update(
        due_at=timezone.now() - timedelta(hours=1)
    )

    mock_email = MagicMock()
    with patch("followups.services.get_adapter", return_value=mock_email) as mock_get:
        count = process_due_reminders()

    assert count == 1
    mock_get.assert_called_once_with(t, IntegrationConfig.Kind.EMAIL)
    mock_email.send.assert_called_once()
    send_kwargs = mock_email.send.call_args.kwargs
    assert send_kwargs["to"] == ["a@acme.io"]
    assert "INV-1" in send_kwargs["subject"]

    rem.refresh_from_db()
    assert rem.status == Reminder.Status.SENT

    from audit.models import AuditLog

    assert AuditLog.objects.filter(
        tenant=t, event="followup.sent", payload__reminder_id=rem.id
    ).exists()


@pytest.mark.django_db
def test_process_due_reminders_skips_future_and_already_sent():
    """Only PENDING reminders whose due_at has passed are processed."""
    from followups.models import Reminder
    from followups.services import process_due_reminders
    from tenants import services as tsvc
    from users.models import User
    from django.utils import timezone

    u = User.objects.create_user(email="a@x.io", password="p", username="a")
    t = tsvc.create_tenant(name="A", slug="a", admin=u)

    # Future pending → skip
    Reminder.objects.create(
        tenant=t, subject="future", due_at=timezone.now() + timedelta(days=1)
    )
    # Past but already SENT → skip
    Reminder.objects.create(
        tenant=t,
        subject="done",
        due_at=timezone.now() - timedelta(hours=1),
        status=Reminder.Status.SENT,
    )
    # CANCELLED → skip
    Reminder.objects.create(
        tenant=t,
        subject="cxl",
        due_at=timezone.now() - timedelta(hours=1),
        status=Reminder.Status.CANCELLED,
    )

    mock_email = MagicMock()
    with patch("followups.services.get_adapter", return_value=mock_email):
        count = process_due_reminders()
    assert count == 0
    mock_email.send.assert_not_called()


@pytest.mark.django_db
def test_process_due_reminders_uses_rule_template_when_present():
    """If a rule is attached, its template is filled with the reminder context."""
    from followups.models import FollowupRule, Reminder
    from followups.services import process_due_reminders
    from integrations.models import IntegrationConfig
    from tenants import services as tsvc
    from users.models import User
    from django.utils import timezone

    u = User.objects.create_user(email="a@x.io", password="p", username="a")
    t = tsvc.create_tenant(name="A", slug="a", admin=u)
    IntegrationConfig.objects.create(
        tenant=t,
        kind=IntegrationConfig.Kind.EMAIL,
        is_active=True,
        credentials={"backend": "smtp"},
    )
    rule = FollowupRule.objects.create(
        tenant=t,
        name="Heads up",
        channel=FollowupRule.Channel.EMAIL,
        template="Heads up: {subject} is due on {due_date}.",
    )
    Reminder.objects.create(
        tenant=t,
        rule=rule,
        subject="INV-9",
        due_at=timezone.now() - timedelta(hours=1),
        recipient_email="x@y.io",
        context={"subject": "Invoice INV-9", "due_date": "2026-08-01"},
    )

    mock_email = MagicMock()
    with patch("followups.services.get_adapter", return_value=mock_email):
        process_due_reminders()

    body = mock_email.send.call_args.kwargs["body"]
    assert "Heads up: Invoice INV-9 is due on 2026-08-01." in body


@pytest.mark.django_db(transaction=True)
def test_issue_invoice_creates_pending_reminder_via_plan5_hook():
    """invoices.services.issue_invoice() schedules a reminder (Plan 5 hook)."""
    from datetime import date
    from unittest.mock import MagicMock, patch

    from followups.models import Reminder
    from integrations.models import IntegrationConfig
    from invoices import services as inv_svc
    from invoices.models import Invoice
    from onboarding.models import Client
    from tenants import services as tsvc
    from users.models import User

    u = User.objects.create_user(email="a@x.io", password="p", username="a")
    t = tsvc.create_tenant(name="A", slug="a", admin=u)
    c = Client.objects.create(tenant=t, name="Acme", email="a@acme.io")
    IntegrationConfig.objects.create(
        tenant=t,
        kind=IntegrationConfig.Kind.EMAIL,
        is_active=True,
        credentials={"backend": "smtp"},
    )
    IntegrationConfig.objects.create(
        tenant=t,
        kind=IntegrationConfig.Kind.STORAGE,
        is_active=True,
        vendor="minio",
        credentials={"bucket": "wa"},
    )
    IntegrationConfig.objects.create(
        tenant=t,
        kind=IntegrationConfig.Kind.BILLING,
        is_active=True,
        credentials={"base_url": "http://in", "token": "tok"},
    )
    inv = Invoice.objects.create(
        tenant=t, client=c, number="INV-1", due_date=date(2026, 12, 31)
    )

    mock_storage = MagicMock()
    mock_storage.put.return_value = f"invoices/{t.id}/INV-1.pdf"
    mock_billing = MagicMock()
    mock_billing.push_invoice.return_value = "inv_42"
    mock_email = MagicMock()

    def fake_get(tenant, kind, vendor="minio"):
        if kind == IntegrationConfig.Kind.STORAGE:
            return mock_storage
        if kind == IntegrationConfig.Kind.BILLING:
            return mock_billing
        if kind == IntegrationConfig.Kind.EMAIL:
            return mock_email
        raise AssertionError(f"unexpected kind: {kind}")

    with patch("invoices.services.get_adapter", side_effect=fake_get):
        inv_svc.issue_invoice(invoice=inv)

    rems = list(Reminder.objects.filter(tenant=t, subject__contains="INV-1"))
    assert len(rems) == 1
    rem = rems[0]
    assert rem.status == Reminder.Status.PENDING
    assert rem.recipient_email == "a@acme.io"
    assert rem.due_at.date() == date(2026, 12, 24)
