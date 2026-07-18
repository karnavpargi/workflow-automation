# ruff: noqa: I001, F401
"""Tests for Invoice, LineItem, and RecurringSchedule models."""

import pytest
from datetime import date
from decimal import Decimal
from django.utils import timezone

from invoices.models import Invoice, LineItem, RecurringSchedule


@pytest.mark.django_db
def test_create_invoice_with_lines_and_total():
    """An invoice has lines and a total (computed from line items)."""
    from tenants import services as tsvc
    from users.models import User
    from onboarding.models import Client

    u = User.objects.create_user(email="a@x.io", password="p", username="a")
    t = tsvc.create_tenant(name="A", slug="a", admin=u)
    c = Client.objects.create(tenant=t, name="Acme", email="a@acme.io")
    inv = Invoice.objects.create(
        tenant=t,
        client=c,
        number="INV-1",
        due_date=date(2026, 12, 31),
    )
    LineItem.objects.create(
        invoice=inv, description="Web", quantity=1, unit_price=Decimal("100")
    )
    LineItem.objects.create(
        invoice=inv, description="Hosting", quantity=2, unit_price=Decimal("50")
    )
    inv.save()  # Triggers auto-compute of total from lines
    assert inv.lines.count() == 2
    assert inv.total == Decimal("200.00")


@pytest.mark.django_db
def test_recurring_schedule_next_run_defaults_to_today():
    """A new recurring schedule's next_run defaults to today."""
    from tenants import services as tsvc
    from users.models import User
    from onboarding.models import Client

    u = User.objects.create_user(email="a@x.io", password="p", username="a")
    t = tsvc.create_tenant(name="A", slug="a", admin=u)
    c = Client.objects.create(tenant=t, name="Acme", email="a@acme.io")
    sched = RecurringSchedule.objects.create(
        tenant=t,
        client=c,
        template_lines=[],
        cadence="monthly",
    )
    assert sched.next_run == timezone.now().date()
