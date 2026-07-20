"""Tests for the dataentry DRF API."""

import hashlib
import hmac

import pytest
from rest_framework.test import APIClient


@pytest.fixture
def authed_client(db):
    """Return (APIClient, user, tenant_slug) for a freshly-created tenant+admin."""
    from tenants import services as tsvc
    from users.models import User

    u = User.objects.create_user(email="a@x.io", password="p", username="a")
    tsvc.create_tenant(name="A", slug="a", admin=u)
    c = APIClient()
    c.force_authenticate(user=u)
    return c, u, "a"


@pytest.mark.django_db
def test_form_submit_creates_pending_record(authed_client):
    """POST /api/dataentry/form/ creates a PENDING record in caller's tenant."""
    from dataentry.models import DataEntryRecord

    client, _user, slug = authed_client
    r = client.post(
        "/api/dataentry/form/",
        {"fields": {"name": "Acme", "email": "a@acme.io"}},
        format="json",
        HTTP_X_TENANT_SLUG=slug,
    )
    assert r.status_code == 201, r.data
    assert r.data["source"] == "form"
    assert r.data["status"] == "pending"
    assert DataEntryRecord.objects.filter(source="form").count() == 1


@pytest.mark.django_db
def test_csv_upload_creates_one_record_per_row(authed_client):
    """POST /api/dataentry/csv/ with multipart creates one record per row."""
    from django.core.files.uploadedfile import SimpleUploadedFile

    from dataentry.models import DataEntryRecord

    client, _user, slug = authed_client
    csv_bytes = b"name,email\nAcme,a@a.io\nBeta,b@b.io\n"
    upload = SimpleUploadedFile("data.csv", csv_bytes, content_type="text/csv")
    r = client.post(
        "/api/dataentry/csv/",
        data={"file": upload},
        HTTP_X_TENANT_SLUG=slug,
    )
    assert r.status_code == 201, r.data
    assert r.data["count"] == 2
    assert DataEntryRecord.objects.count() == 2


@pytest.mark.django_db
def test_webhook_receives_signed_payload_creates_record():
    """POST /api/dataentry/webhook/{slug}/ accepts a signed JSON body."""
    import json

    from dataentry.models import DataEntryRecord
    from tenants import services as tsvc
    from users.models import User

    u = User.objects.create_user(email="a@x.io", password="p", username="a")
    t = tsvc.create_tenant(name="A", slug="a", admin=u)
    t.webhook_secret = "shh"
    t.save(update_fields=["webhook_secret"])
    body = json.dumps({"name": "Acme"}).encode("utf-8")
    sig = hmac.new(b"shh", body, hashlib.sha256).hexdigest()

    c = APIClient()  # unauthenticated
    r = c.post(
        f"/api/dataentry/webhook/{t.slug}/",
        data=body,
        content_type="application/json",
        HTTP_X_SIGNATURE=sig,
    )
    assert r.status_code == 201, r.data
    assert DataEntryRecord.objects.filter(source="webhook").count() == 1


@pytest.mark.django_db
def test_webhook_rejects_bad_signature():
    """A bad or missing X-Signature returns 401."""
    from tenants import services as tsvc
    from users.models import User

    u = User.objects.create_user(email="a@x.io", password="p", username="a")
    t = tsvc.create_tenant(name="A", slug="a", admin=u)
    t.webhook_secret = "shh"
    t.save(update_fields=["webhook_secret"])

    c = APIClient()
    r = c.post(
        f"/api/dataentry/webhook/{t.slug}/",
        data=b'{"name":"x"}',
        content_type="application/json",
    )
    assert r.status_code == 401


@pytest.mark.django_db
def test_list_records_scoped_to_tenant(authed_client):
    """GET /api/dataentry/records/ returns only the caller's tenant's records."""
    from dataentry.models import DataEntryRecord
    from tenants import services as tsvc
    from users.models import User

    client, user, slug = authed_client
    t_a = user.memberships.first().tenant
    DataEntryRecord.objects.create(tenant=t_a, source="form", raw={"a": 1})
    ub = User.objects.create_user(email="b@x.io", password="p", username="b")
    tb = tsvc.create_tenant(name="B", slug="b", admin=ub)
    DataEntryRecord.objects.create(tenant=tb, source="form", raw={"b": 2})
    r = client.get("/api/dataentry/records/", HTTP_X_TENANT_SLUG=slug)
    assert r.status_code == 200
    assert len(r.data) == 1
