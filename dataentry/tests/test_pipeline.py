# ruff: noqa: I001, F401
"""Tests for the validate -> map -> dispatch pipeline."""

import pytest


def _make_pending(tenant, *, target_type: str = "contact", **raw):
    """Helper: create a tenant + a PENDING DataEntryRecord."""
    from dataentry.models import DataEntryRecord

    rec = DataEntryRecord.objects.create(
        tenant=tenant, source=DataEntryRecord.Source.FORM, raw=raw
    )
    if target_type != "contact":
        rec.target_type = target_type
        rec.save(update_fields=["target_type"])
    return rec


def _tenant(slug: str = "a"):
    from tenants import services as tsvc
    from users.models import User

    u = User.objects.create_user(email=f"a@{slug}.io", password="p", username=slug)
    return tsvc.create_tenant(name=slug.upper(), slug=slug, admin=u)


@pytest.mark.django_db
def test_process_record_happy_path_creates_contact_and_marks_dispatched():
    """A contact record with name+email is mapped, validated, dispatched."""
    from dataentry.models import DataEntryRecord
    from dataentry.tasks import process_record
    from onboarding.models import Client

    t = _tenant()
    rec = _make_pending(t, name="Acme", email="a@acme.io")

    process_record(rec.id)

    rec.refresh_from_db()
    assert rec.status == DataEntryRecord.Status.DISPATCHED
    assert rec.mapped["name"] == "Acme"
    assert rec.mapped["email"] == "a@acme.io"
    assert rec.error == ""
    assert Client.objects.filter(tenant=t, email="a@acme.io").exists()


@pytest.mark.django_db
def test_process_record_marks_invalid_when_required_field_missing():
    """A contact without email is marked INVALID with an explanatory error."""
    from dataentry.models import DataEntryRecord
    from dataentry.tasks import process_record

    t = _tenant()
    rec = _make_pending(t, name="NoEmail")  # no email

    process_record(rec.id)

    rec.refresh_from_db()
    assert rec.status == DataEntryRecord.Status.INVALID
    assert "email" in rec.error.lower()
    assert rec.mapped == {}  # mapping didn't fail; validation did


@pytest.mark.django_db
def test_process_record_invoice_dispatch_creates_draft_invoice():
    """An invoice target creates a draft Invoice (status=draft)."""
    from dataentry.models import DataEntryRecord
    from dataentry.tasks import process_record
    from invoices.models import Invoice

    t = _tenant()
    rec = DataEntryRecord.objects.create(
        tenant=t,
        source=DataEntryRecord.Source.WEBHOOK,
        target_type="invoice",
        raw={
            "client_email": "lead@x.io",
            "client_name": "Lead Co",
            "number": "INV-1",
            "total": "100.00",
            "due_date": "2026-12-31",
        },
    )

    process_record(rec.id)

    rec.refresh_from_db()
    assert rec.status == DataEntryRecord.Status.DISPATCHED
    inv = Invoice.objects.get(tenant=t, number="INV-1")
    assert inv.status == Invoice.Status.DRAFT
    assert inv.client.email == "lead@x.io"


@pytest.mark.django_db
def test_process_record_other_target_dispatches_without_creating_object():
    """An ``other`` target_type just marks the record DISPATCHED."""
    from dataentry.models import DataEntryRecord
    from dataentry.tasks import process_record

    t = _tenant()
    rec = DataEntryRecord.objects.create(
        tenant=t,
        source=DataEntryRecord.Source.WEBHOOK,
        target_type="other",
        raw={"anything": "goes"},
    )

    process_record(rec.id)

    rec.refresh_from_db()
    assert rec.status == DataEntryRecord.Status.DISPATCHED
