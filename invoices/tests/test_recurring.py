"""Tests for the recurring invoice Beat job."""

from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest
from django.utils import timezone

from invoices.models import RecurringSchedule
from invoices.tasks import check_recurring_invoices


@pytest.mark.django_db(transaction=True)
def test_check_recurring_invoices_issues_due_schedules(settings):
    """The Beat job issues due schedules and advances their next_run."""
    from invoices.models import Invoice
    from onboarding.models import Client
    from tenants import services as tsvc
    from users.models import User

    u = User.objects.create_user(email="a@x.io", password="p", username="a")
    t = tsvc.create_tenant(name="A", slug="a", admin=u)
    c = Client.objects.create(tenant=t, name="Acme", email="a@acme.io")

    past = timezone.now().date() - timedelta(days=5)
    sched = RecurringSchedule.objects.create(
        tenant=t,
        client=c,
        template_lines=[
            {"description": "Hosting", "quantity": 1, "unit_price": 100},
        ],
        cadence="monthly",
        next_run=past,
        is_active=True,
    )

    with patch("invoices.tasks.issue_invoice_from_schedule") as mock_issue:
        mock_issue.return_value = MagicMock(spec=Invoice)
        count = check_recurring_invoices()

    assert count == 1
    mock_issue.assert_called_once_with(sched)
    sched.refresh_from_db()
    # next_run should be advanced by ~30 days
    assert sched.next_run > past


@pytest.mark.django_db(transaction=True)
def test_check_recurring_invoices_disables_after_three_consecutive_failures(settings):
    """A schedule that fails three times in a row is auto-disabled."""
    from onboarding.models import Client
    from tenants import services as tsvc
    from users.models import User

    u = User.objects.create_user(email="a@x.io", password="p", username="a")
    t = tsvc.create_tenant(name="A", slug="a", admin=u)
    c = Client.objects.create(tenant=t, name="Acme", email="a@acme.io")

    past = timezone.now().date() - timedelta(days=5)
    sched = RecurringSchedule.objects.create(
        tenant=t,
        client=c,
        template_lines=[
            {"description": "Hosting", "quantity": 1, "unit_price": 100},
        ],
        cadence="monthly",
        next_run=past,
        is_active=True,
    )

    with patch("invoices.tasks.issue_invoice_from_schedule") as mock_issue:
        mock_issue.side_effect = RuntimeError("client deleted")
        # Three failed calls across three days
        for _ in range(3):
            check_recurring_invoices()
            # Simulate the next day's Beat run by rewinding next_run
            sched.refresh_from_db()
            sched.next_run = timezone.now().date() - timedelta(days=1)
            sched.save(update_fields=["next_run"])

    sched.refresh_from_db()
    assert sched.consecutive_failures == 3
    assert sched.is_active is False


@pytest.mark.django_db(transaction=True)
def test_check_recurring_invoices_resets_consecutive_failures_on_success(settings):
    """A successful run resets consecutive_failures back to 0."""
    from invoices.models import Invoice
    from onboarding.models import Client
    from tenants import services as tsvc
    from users.models import User

    u = User.objects.create_user(email="a@x.io", password="p", username="a")
    t = tsvc.create_tenant(name="A", slug="a", admin=u)
    c = Client.objects.create(tenant=t, name="Acme", email="a@acme.io")

    past = timezone.now().date() - timedelta(days=5)
    sched = RecurringSchedule.objects.create(
        tenant=t,
        client=c,
        template_lines=[
            {"description": "Hosting", "quantity": 1, "unit_price": 100},
        ],
        cadence="monthly",
        next_run=past,
        is_active=True,
        consecutive_failures=2,
    )

    with patch("invoices.tasks.issue_invoice_from_schedule") as mock_issue:
        mock_issue.return_value = MagicMock(spec=Invoice)
        check_recurring_invoices()

    sched.refresh_from_db()
    assert sched.consecutive_failures == 0
    assert sched.is_active is True
