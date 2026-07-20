# ruff: noqa: I001, F401
"""Tests for the DataEntryRecord model."""

import pytest


@pytest.mark.django_db
def test_create_data_entry_record_defaults_to_pending():
    """A new DataEntryRecord is PENDING with empty raw/mapped dicts."""
    from dataentry.models import DataEntryRecord
    from tenants import services as tsvc
    from users.models import User

    u = User.objects.create_user(email="a@x.io", password="p", username="a")
    t = tsvc.create_tenant(name="A", slug="a", admin=u)
    rec = DataEntryRecord.objects.create(tenant=t, source=DataEntryRecord.Source.FORM)
    assert rec.status == DataEntryRecord.Status.PENDING
    assert rec.status == "pending"
    assert rec.raw == {}
    assert rec.mapped == {}
    assert rec.target_type == "contact"
    assert rec.error == ""


@pytest.mark.django_db
def test_data_entry_record_stores_raw_and_mapped_payloads():
    """The raw and mapped fields hold arbitrary JSON payloads."""
    from dataentry.models import DataEntryRecord
    from tenants import services as tsvc
    from users.models import User

    u = User.objects.create_user(email="a@x.io", password="p", username="a")
    t = tsvc.create_tenant(name="A", slug="a", admin=u)
    rec = DataEntryRecord.objects.create(
        tenant=t,
        source=DataEntryRecord.Source.CSV,
        raw={"row": {"name": "Acme", "email": "a@a.io"}},
        mapped={"name": "Acme", "email": "a@a.io"},
        target_type="contact",
    )
    rec.refresh_from_db()
    assert rec.raw["row"]["name"] == "Acme"
    assert rec.mapped["email"] == "a@a.io"
    assert rec.source == "csv"


@pytest.mark.django_db
def test_tenant_related_name_returns_records():
    """``tenant.dataentry_records`` exposes the inverse FK relation."""
    from dataentry.models import DataEntryRecord
    from tenants import services as tsvc
    from users.models import User

    u = User.objects.create_user(email="a@x.io", password="p", username="a")
    t = tsvc.create_tenant(name="A", slug="a", admin=u)
    DataEntryRecord.objects.create(tenant=t, source=DataEntryRecord.Source.FORM)
    DataEntryRecord.objects.create(tenant=t, source=DataEntryRecord.Source.CSV)
    assert t.dataentry_records.count() == 2


@pytest.mark.django_db
def test_data_entry_record_records_error_message():
    """Validation failures are captured in the error field."""
    from dataentry.models import DataEntryRecord
    from tenants import services as tsvc
    from users.models import User

    u = User.objects.create_user(email="a@x.io", password="p", username="a")
    t = tsvc.create_tenant(name="A", slug="a", admin=u)
    rec = DataEntryRecord.objects.create(
        tenant=t,
        source=DataEntryRecord.Source.WEBHOOK,
        status=DataEntryRecord.Status.INVALID,
        error="missing required field: email",
    )
    rec.refresh_from_db()
    assert rec.status == "invalid"
    assert "missing required field: email" in rec.error
