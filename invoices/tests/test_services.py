"""Tests for the issue_invoice service (Flow B)."""

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from django.core import mail


@pytest.mark.django_db(transaction=True)
def test_issue_invoice_renders_emails_pushes_and_marks_issued(settings):
    """issue_invoice renders PDF, stores, pushes to billing, emails, and marks ISSUED.

    Adapters (storage, billing, email) are mocked via ``get_adapter`` so
    the test exercises the service orchestration without hitting real
    vendors. Chat is intentionally not configured; the service swallows
    the ``AdapterNotConfigured`` so the test still passes.
    """
    from integrations.models import IntegrationConfig
    from invoices import services as inv_svc
    from invoices.models import Invoice, LineItem
    from onboarding.models import Client
    from tenants import services as tsvc
    from users.models import User

    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

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
        tenant=t,
        client=c,
        number="INV-1",
        due_date=date(2026, 12, 31),
    )
    LineItem.objects.create(
        invoice=inv, description="Web", quantity=1, unit_price=Decimal("100")
    )
    inv.save()

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

    mock_storage.put.assert_called_once()
    mock_billing.push_invoice.assert_called_once()
    mock_email.send.assert_called_once()

    inv.refresh_from_db()
    assert inv.status == Invoice.Status.ISSUED
    assert inv.vendor_id == "inv_42"
    assert inv.pdf_path == f"invoices/{t.id}/INV-1.pdf"

    assert len(mail.outbox) == 0
