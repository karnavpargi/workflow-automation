# ruff: noqa: I001, F401
"""Tests for the four source adapters in :mod:`dataentry.adapters`."""

import hashlib
import hmac
from datetime import date

import pytest


def _make_tenant(slug: str = "a") -> object:
    """Helper: create an admin user + tenant and return the tenant."""
    from tenants import services as tsvc
    from users.models import User

    u = User.objects.create_user(email=f"a@{slug}.io", password="p", username=slug)
    return tsvc.create_tenant(name=slug.upper(), slug=slug, admin=u)


@pytest.mark.django_db
def test_ingest_form_creates_pending_record_with_raw_payload():
    """ingest_form stores the form fields verbatim in raw."""
    from dataentry.adapters.form import ingest_form
    from dataentry.models import DataEntryRecord

    t = _make_tenant()
    rec = ingest_form(t, {"name": "Acme", "email": "a@acme.io"})
    assert rec.status == DataEntryRecord.Status.PENDING
    assert rec.source == DataEntryRecord.Source.FORM
    assert rec.raw == {"name": "Acme", "email": "a@acme.io"}


@pytest.mark.django_db
def test_ingest_csv_creates_one_record_per_data_row():
    """ingest_csv skips the header row and emits one record per data row."""
    import io

    from dataentry.adapters.csv_xlsx import ingest_csv
    from dataentry.models import DataEntryRecord

    t = _make_tenant()
    payload = "name,email\nAcme,a@a.io\nBeta,b@b.io\n"
    recs = ingest_csv(t, io.BytesIO(payload.encode("utf-8")))
    assert len(recs) == 2
    assert recs[0].source == DataEntryRecord.Source.CSV
    assert recs[0].raw == {"name": "Acme", "email": "a@a.io"}
    assert recs[1].raw == {"name": "Beta", "email": "b@b.io"}
    assert all(r.status == DataEntryRecord.Status.PENDING for r in recs)


@pytest.mark.django_db
def test_ingest_xlsx_creates_one_record_per_data_row():
    """ingest_xlsx reads the first sheet, header row + data rows."""
    import io

    from openpyxl import Workbook

    from dataentry.adapters.csv_xlsx import ingest_xlsx
    from dataentry.models import DataEntryRecord

    wb = Workbook()
    ws = wb.active
    ws.append(["name", "email"])
    ws.append(["Acme", "a@a.io"])
    ws.append(["Beta", "b@b.io"])
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)

    t = _make_tenant()
    recs = ingest_xlsx(t, buf)
    assert len(recs) == 2
    assert recs[0].raw == {"name": "Acme", "email": "a@a.io"}
    assert recs[0].source == DataEntryRecord.Source.CSV


@pytest.mark.django_db
def test_ingest_email_extracts_from_subject_body():
    """ingest_email uses mail-parser to pull From/Subject/Body into raw."""
    from dataentry.adapters.email_basic import ingest_email
    from dataentry.models import DataEntryRecord

    eml = (
        b"From: Lead <lead@x.io>\r\n"
        b"To: ops@agency.io\r\n"
        b"Subject: Quote request\r\n"
        b"\r\n"
        b"Please send pricing.\r\n"
    )
    t = _make_tenant()
    rec = ingest_email(t, eml)
    assert rec.source == DataEntryRecord.Source.EMAIL
    assert rec.status == DataEntryRecord.Status.PENDING
    assert rec.raw["from"] == "lead@x.io"
    assert rec.raw["subject"] == "Quote request"
    assert "Please send pricing" in rec.raw["body"]


@pytest.mark.django_db
def test_ingest_webhook_verifies_hmac_and_stores_payload():
    """ingest_webhook validates X-Signature (HMAC-SHA256 hex) and stores JSON."""
    import json

    from dataentry.adapters.webhook import ingest_webhook
    from dataentry.models import DataEntryRecord

    t = _make_tenant()
    t.webhook_secret = "shh-its-a-secret"
    t.save(update_fields=["webhook_secret"])
    body = json.dumps({"name": "Acme", "email": "a@a.io"}).encode("utf-8")
    sig = hmac.new(b"shh-its-a-secret", body, hashlib.sha256).hexdigest()

    rec = ingest_webhook(t, body, signature=sig)
    assert rec.source == DataEntryRecord.Source.WEBHOOK
    assert rec.raw == {"name": "Acme", "email": "a@a.io"}


@pytest.mark.django_db
def test_ingest_webhook_rejects_bad_signature():
    """A wrong or missing X-Signature raises InvalidSignature."""
    import json

    import pytest as _pytest

    from dataentry.adapters.webhook import InvalidSignature, ingest_webhook

    t = _make_tenant()
    t.webhook_secret = "shh-its-a-secret"
    t.save(update_fields=["webhook_secret"])
    body = json.dumps({"name": "Acme"}).encode("utf-8")

    with _pytest.raises(InvalidSignature):
        ingest_webhook(t, body, signature="deadbeef")
    with _pytest.raises(InvalidSignature):
        ingest_webhook(t, body, signature=None)
