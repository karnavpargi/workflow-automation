"""Tests for invoice PDF generation."""

import pytest


@pytest.mark.django_db
def test_render_invoice_pdf():
    """render_invoice_pdf returns bytes starting with %PDF."""
    from datetime import date
    from decimal import Decimal

    from invoices.models import Invoice, LineItem
    from invoices.pdf import render_invoice_pdf
    from onboarding.models import Client
    from tenants import services as tsvc
    from users.models import User

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
    pdf = render_invoice_pdf(inv)
    assert pdf.startswith(b"%PDF")
