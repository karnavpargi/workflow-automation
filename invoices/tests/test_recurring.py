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
