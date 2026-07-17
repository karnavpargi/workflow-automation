# Integrations Adapters Implementation Plan (Plan 3 of 11)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build pluggable free/OSS integration adapters for CRM (SuiteCRM), Billing (Invoice Ninja), Storage (Nextcloud + MinIO), Chat (Mattermost), and Email (Django SMTP / Postfix).

**Architecture:** Abstract base adapters in `integrations/base.py`. Each vendor adapter implements the interface. Tenant config stored in `IntegrationConfig`. HTTP via `httpx`. Tests use `httpx_mock` / `respx`. Live tests against Dockerized vendors gated by `MAKE_REAL=1`.

**Tech Stack:** Django, httpx, respx, free/OSS only (SuiteCRM, Invoice Ninja, Nextcloud, MinIO, Mattermost, Postfix).

**Depends on:** Plan 1.

---

## File Structure

```
integrations/
├── base.py                 # abstract adapters + typed exceptions
├── models.py               # IntegrationConfig (tenant, kind, credentials JSON)
├── services.py             # get_adapter(tenant, kind)
├── crm/suitecrm.py
├── billing/invoice_ninja.py
├── storage/nextcloud.py
├── storage/minio_client.py
├── chat/mattermost.py
├── email/django_smtp.py
├── tests/
│   ├── test_base.py
│   ├── test_suitecrm.py
│   ├── test_invoice_ninja.py
│   ├── test_nextcloud.py
│   ├── test_minio.py
│   ├── test_mattermost.py
│   └── test_email.py
docker-compose.integrations.yml   # optional SuiteCRM / Invoice Ninja / etc.
```

---

### Task 1: Base interfaces + exceptions

- [ ] **Step 1: Write failing test `integrations/tests/test_base.py`**

```python
"""Tests for adapter base interfaces."""
from integrations.base import (
    BillingAdapter,
    ChatAdapter,
    CrmAdapter,
    EmailAdapter,
    IntegrationAuthFailed,
    IntegrationRateLimited,
    IntegrationUnavailable,
    StorageAdapter,
)


def test_exceptions_are_distinct():
    """Typed exceptions exist and are independent classes."""
    assert issubclass(IntegrationUnavailable, Exception)
    assert IntegrationAuthFailed is not IntegrationRateLimited


def test_abstract_adapters_require_methods():
    """Abstract methods raise TypeError if not implemented."""
    import pytest
    with pytest.raises(TypeError):
        CrmAdapter()  # type: ignore[abstract]
```

- [ ] **Step 2: Implement `integrations/base.py`**

```python
"""Abstract adapter interfaces and typed integration exceptions.

Every vendor adapter implements one of these interfaces so the rest of
the platform never depends on vendor-specific HTTP details.
"""
from abc import ABC, abstractmethod
from typing import Any


class IntegrationUnavailable(Exception):
    """Vendor is down or unreachable; retryable."""


class IntegrationAuthFailed(Exception):
    """Credentials rejected; not retryable without config change."""


class IntegrationRateLimited(Exception):
    """Vendor rate limit hit; retryable after backoff."""


class CrmAdapter(ABC):
    """CRM operations against SuiteCRM (or compatible)."""

    @abstractmethod
    def upsert_contact(self, contact: dict[str, Any]) -> str:
        """Create or update a contact; return vendor id.

        Args:
            contact: Contact fields (email, name, ...).

        Returns:
            Vendor-side contact id.
        """


class BillingAdapter(ABC):
    """Billing operations against Invoice Ninja."""

    @abstractmethod
    def push_invoice(self, invoice: dict[str, Any]) -> str:
        """Push an invoice and return vendor id.

        Args:
            invoice: Invoice payload.

        Returns:
            Vendor-side invoice id.
        """


class StorageAdapter(ABC):
    """Document / object storage operations."""

    @abstractmethod
    def put(self, path: str, data: bytes, content_type: str) -> str:
        """Store bytes at path; return URL or path.

        Args:
            path: Object path.
            data: File bytes.
            content_type: MIME type.

        Returns:
            Accessible path or URL.
        """

    @abstractmethod
    def get_url(self, path: str, expires_seconds: int = 3600) -> str:
        """Return a time-limited URL for the object.

        Args:
            path: Object path.
            expires_seconds: Link lifetime.

        Returns:
            Signed or temporary URL.
        """


class ChatAdapter(ABC):
    """Chat notifications (Mattermost)."""

    @abstractmethod
    def post(self, channel: str, text: str) -> None:
        """Post a message to a channel.

        Args:
            channel: Channel id or webhook name.
            text: Message body.
        """


class EmailAdapter(ABC):
    """Outbound email."""

    @abstractmethod
    def send(
        self,
        *,
        to: list[str],
        subject: str,
        body: str,
        attachments: list[tuple[str, bytes, str]] | None = None,
    ) -> None:
        """Send an email.

        Args:
            to: Recipient addresses.
            subject: Subject line.
            body: Plain-text or HTML body.
            attachments: Optional list of (filename, bytes, content_type).
        """
```

- [ ] **Step 3: Tests PASS + commit**

```bash
python manage.py startapp integrations
# add to INSTALLED_APPS
pytest integrations/tests/test_base.py -v
git add integrations/ && git commit -m "feat(integrations): abstract adapters + typed exceptions"
```

---

### Task 2: IntegrationConfig model + get_adapter

- [ ] **Step 1: Write failing test for model + factory**

```python
"""Tests for IntegrationConfig and get_adapter."""
import pytest
from integrations.models import IntegrationConfig
from integrations.services import get_adapter
from integrations.base import EmailAdapter


@pytest.mark.django_db
def test_get_adapter_email_returns_smtp():
    """Configured email adapter returns EmailAdapter implementation."""
    from tenants import services as tsvc
    from users.models import User
    u = User.objects.create_user(email="a@x.io", password="p", username="a")
    t = tsvc.create_tenant(name="A", slug="a", admin=u)
    IntegrationConfig.objects.create(
        tenant=t, kind=IntegrationConfig.Kind.EMAIL,
        credentials={"backend": "smtp"}, is_active=True,
    )
    adapter = get_adapter(t, IntegrationConfig.Kind.EMAIL)
    assert isinstance(adapter, EmailAdapter)
```

- [ ] **Step 2: Implement model + service**

```python
# integrations/models.py
"""Per-tenant integration configuration."""
from django.db import models


class IntegrationConfig(models.Model):
    """Credentials and flags for one integration kind per tenant.

    Attributes:
        tenant: Owning tenant.
        kind: One of CRM, BILLING, STORAGE, CHAT, EMAIL.
        credentials: JSON blob of vendor credentials (encrypted at rest later).
        is_active: Whether this config is currently used.
    """

    class Kind(models.TextChoices):
        """Supported integration kinds."""

        CRM = "crm", "CRM"
        BILLING = "billing", "Billing"
        STORAGE = "storage", "Storage"
        CHAT = "chat", "Chat"
        EMAIL = "email", "Email"

    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.CASCADE, related_name="integrations"
    )
    kind = models.CharField(max_length=20, choices=Kind.choices)
    credentials = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "kind"], name="uniq_tenant_kind"
            ),
        ]


# integrations/services.py
"""Factory for tenant-scoped adapters."""
from integrations.base import EmailAdapter
from integrations.email.django_smtp import DjangoSmtpEmailAdapter
from integrations.models import IntegrationConfig


class AdapterNotConfigured(Exception):
    """Raised when a tenant has no active config for the requested kind."""


def get_adapter(tenant, kind: str):
    """Return an adapter instance for the tenant and kind.

    Args:
        tenant: Tenant instance.
        kind: IntegrationConfig.Kind value.

    Returns:
        Adapter implementing the corresponding abstract interface.

    Raises:
        AdapterNotConfigured: if no active config exists.
    """
    try:
        cfg = IntegrationConfig.objects.get(
            tenant=tenant, kind=kind, is_active=True
        )
    except IntegrationConfig.DoesNotExist as exc:
        raise AdapterNotConfigured(kind) from exc
    if kind == IntegrationConfig.Kind.EMAIL:
        return DjangoSmtpEmailAdapter(cfg.credentials)
    # other kinds wired in later tasks
    raise AdapterNotConfigured(kind)
```

- [ ] **Step 3: Migrate + tests PASS + commit**

```bash
python manage.py makemigrations integrations && python manage.py migrate
pytest integrations/tests/ -v
git add integrations/ && git commit -m "feat(integrations): IntegrationConfig + get_adapter factory"
```

---

### Task 3: Email adapter (Django SMTP)

- [ ] **Step 1: Failing test with django.core.mail.outbox**

```python
"""Tests for Django SMTP email adapter."""
import pytest
from django.core import mail
from integrations.email.django_smtp import DjangoSmtpEmailAdapter


@pytest.mark.django_db
def test_send_uses_django_outbox(settings):
    """EmailAdapter.send deposits a message in the locmem outbox."""
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    adapter = DjangoSmtpEmailAdapter({})
    adapter.send(to=["a@x.io"], subject="Hi", body="Hello")
    assert len(mail.outbox) == 1
    assert mail.outbox[0].subject == "Hi"
```

- [ ] **Step 2: Implement**

```python
# integrations/email/django_smtp.py
"""Email adapter backed by Django's email backend (SMTP / locmem)."""
from django.core.mail import EmailMessage

from integrations.base import EmailAdapter


class DjangoSmtpEmailAdapter(EmailAdapter):
    """Send email via Django's configured EMAIL_BACKEND.

    Args:
        credentials: Unused for now; reserved for per-tenant SMTP.
    """

    def __init__(self, credentials: dict) -> None:
        """Store credentials (future per-tenant SMTP).

        Args:
            credentials: Vendor credentials dict.
        """
        self.credentials = credentials

    def send(
        self,
        *,
        to: list[str],
        subject: str,
        body: str,
        attachments: list[tuple[str, bytes, str]] | None = None,
    ) -> None:
        """Send an email via Django.

        Args:
            to: Recipients.
            subject: Subject line.
            body: Body text.
            attachments: Optional (filename, bytes, content_type) list.
        """
        msg = EmailMessage(subject=subject, body=body, to=to)
        for name, data, ctype in attachments or []:
            msg.attach(name, data, ctype)
        msg.send(fail_silently=False)
```

- [ ] **Step 3: Tests PASS + commit**

```bash
pytest integrations/tests/test_email.py -v
git add integrations/ && git commit -m "feat(integrations): Django SMTP email adapter"
```

---

### Task 4: Mattermost chat adapter

- [ ] **Step 1: Failing test with respx/httpx mock**

```python
"""Tests for Mattermost chat adapter."""
import httpx
import pytest
import respx
from integrations.chat.mattermost import MattermostChatAdapter
from integrations.base import IntegrationUnavailable


@respx.mock
def test_post_sends_webhook():
    """post() POSTs JSON to the configured webhook URL."""
    route = respx.post("http://mm/hooks/x").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )
    adapter = MattermostChatAdapter({"webhook_url": "http://mm/hooks/x"})
    adapter.post(channel="ops", text="hello")
    assert route.called


@respx.mock
def test_post_unavailable_raises():
    """5xx from Mattermost raises IntegrationUnavailable."""
    respx.post("http://mm/hooks/x").mock(return_value=httpx.Response(503))
    adapter = MattermostChatAdapter({"webhook_url": "http://mm/hooks/x"})
    with pytest.raises(IntegrationUnavailable):
        adapter.post(channel="ops", text="hello")
```

- [ ] **Step 2: Implement**

```python
# integrations/chat/mattermost.py
"""Mattermost webhook chat adapter."""
import httpx

from integrations.base import ChatAdapter, IntegrationUnavailable


class MattermostChatAdapter(ChatAdapter):
    """Post messages via an incoming webhook.

    Args:
        credentials: Must include ``webhook_url``.
    """

    def __init__(self, credentials: dict) -> None:
        """Store webhook URL.

        Args:
            credentials: Dict with webhook_url.
        """
        self.webhook_url = credentials["webhook_url"]

    def post(self, channel: str, text: str) -> None:
        """Post a message.

        Args:
            channel: Channel name (embedded in text if webhook is fixed).
            text: Message body.

        Raises:
            IntegrationUnavailable: on non-2xx response.
        """
        try:
            r = httpx.post(
                self.webhook_url,
                json={"channel": channel, "text": text},
                timeout=10.0,
            )
            r.raise_for_status()
        except httpx.HTTPError as exc:
            raise IntegrationUnavailable(str(exc)) from exc
```

- [ ] **Step 3: Wire into get_adapter + tests PASS + commit**

```bash
# add httpx and respx to pyproject.toml dependencies / dev
pytest integrations/tests/test_mattermost.py -v
git add integrations/ pyproject.toml
git commit -m "feat(integrations): Mattermost chat adapter"
```

---

### Task 5: MinIO storage adapter

- [ ] **Step 1: Failing test with mocked boto3/minio client** (use free `minio` Python SDK)

```python
"""Tests for MinIO storage adapter."""
from unittest.mock import MagicMock, patch
from integrations.storage.minio_client import MinioStorageAdapter


def test_put_returns_path():
    """put() uploads bytes and returns the object path."""
    with patch("integrations.storage.minio_client.Minio") as MockMinio:
        client = MagicMock()
        MockMinio.return_value = client
        adapter = MinioStorageAdapter({
            "endpoint": "localhost:9000",
            "access_key": "minio",
            "secret_key": "minio123",
            "bucket": "wa",
            "secure": False,
        })
        path = adapter.put("invoices/1.pdf", b"%PDF", "application/pdf")
        assert path == "invoices/1.pdf"
        client.put_object.assert_called_once()
```

- [ ] **Step 2: Implement using free `minio` package**

```python
# integrations/storage/minio_client.py
"""MinIO S3-compatible storage adapter."""
from io import BytesIO

from minio import Minio

from integrations.base import StorageAdapter


class MinioStorageAdapter(StorageAdapter):
    """Object storage via MinIO.

    Args:
        credentials: endpoint, access_key, secret_key, bucket, secure.
    """

    def __init__(self, credentials: dict) -> None:
        """Build MinIO client from credentials.

        Args:
            credentials: Connection dict.
        """
        self.bucket = credentials["bucket"]
        self.client = Minio(
            credentials["endpoint"],
            access_key=credentials["access_key"],
            secret_key=credentials["secret_key"],
            secure=credentials.get("secure", False),
        )

    def put(self, path: str, data: bytes, content_type: str) -> str:
        """Upload bytes to MinIO.

        Args:
            path: Object path.
            data: File bytes.
            content_type: MIME type.

        Returns:
            The object path.
        """
        self.client.put_object(
            self.bucket,
            path,
            BytesIO(data),
            length=len(data),
            content_type=content_type,
        )
        return path

    def get_url(self, path: str, expires_seconds: int = 3600) -> str:
        """Presigned GET URL.

        Args:
            path: Object path.
            expires_seconds: Lifetime.

        Returns:
            Presigned URL string.
        """
        from datetime import timedelta
        return self.client.presigned_get_object(
            self.bucket, path, expires=timedelta(seconds=expires_seconds)
        )
```

- [ ] **Step 3: Add `minio` service to `docker-compose.yml` (free image `minio/minio`) + tests PASS + commit**

```bash
pytest integrations/tests/test_minio.py -v
git add integrations/ docker-compose.yml pyproject.toml
git commit -m "feat(integrations): MinIO storage adapter + compose service"
```

---

### Task 6: Nextcloud (WebDAV) storage adapter

- [ ] **Step 1: Failing test with httpx mock for WebDAV PUT/PROPFIND**
- [ ] **Step 2: Implement `NextcloudStorageAdapter` using free WebDAV over httpx**
- [ ] **Step 3: Tests PASS + commit**

```bash
git commit -m "feat(integrations): Nextcloud WebDAV storage adapter"
```

---

### Task 7: Invoice Ninja billing adapter

- [ ] **Step 1: Failing test with respx against Invoice Ninja REST shape**

```python
"""Tests for Invoice Ninja billing adapter."""
import httpx
import respx
from integrations.billing.invoice_ninja import InvoiceNinjaBillingAdapter


@respx.mock
def test_push_invoice_returns_vendor_id():
    """push_invoice posts and returns vendor id."""
    respx.post("http://in/api/v1/invoices").mock(
        return_value=httpx.Response(200, json={"data": {"id": "inv_1"}})
    )
    adapter = InvoiceNinjaBillingAdapter({
        "base_url": "http://in",
        "token": "tok",
    })
    vid = adapter.push_invoice({"amount": 100, "client_id": "c1"})
    assert vid == "inv_1"
```

- [ ] **Step 2: Implement (free Invoice Ninja self-hosted API)**
- [ ] **Step 3: Wire into get_adapter + tests PASS + commit**

```bash
git commit -m "feat(integrations): Invoice Ninja billing adapter"
```

---

### Task 8: SuiteCRM CRM adapter

- [ ] **Step 1: Failing test with respx against SuiteCRM REST**
- [ ] **Step 2: Implement `SuiteCrmAdapter.upsert_contact`**
- [ ] **Step 3: Wire into get_adapter + tests PASS + commit**

```bash
git commit -m "feat(integrations): SuiteCRM CRM adapter"
```

---

### Task 9: Optional live integration compose file

- [ ] **Step 1: Write `docker-compose.integrations.yml`** with free images only:
  - `suitecrm/suitecrm` (or bitnami/suitecrm)
  - Invoice Ninja official image
  - `nextcloud` official
  - `mattermost/mattermost-team-edition` (free Team Edition)
  - MinIO already in main compose
- [ ] **Step 2: Document `MAKE_REAL=1 pytest integrations/tests/ -m live`**
- [ ] **Step 3: Commit**

```bash
git commit -m "docs: optional docker-compose.integrations for live adapter tests"
```

---

## Self-Review

- Free/OSS only: SuiteCRM, Invoice Ninja, Nextcloud, MinIO, Mattermost Team, Postfix/Django SMTP, httpx, minio SDK.
- No paid SaaS.
- Spec adapters all covered.
- Depends on Plan 1 only.
