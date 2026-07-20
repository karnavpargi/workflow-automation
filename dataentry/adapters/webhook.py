"""Webhook ingest adapter.

Verifies an HMAC-SHA256 signature carried in the ``X-Signature`` header
(hex-encoded). The shared secret is per-tenant
(:attr:`tenants.Tenant.webhook_secret`); tenants that have not set one
reject all webhooks.
"""

import hashlib
import hmac
import json

from dataentry.models import DataEntryRecord


class InvalidSignature(Exception):
    """Raised when the X-Signature header does not match the body."""


def ingest_webhook(tenant, body: bytes, *, signature: str | None) -> DataEntryRecord:
    """Verify HMAC and stage the payload as a PENDING record.

    Args:
        tenant: Owning tenant. Must have a non-empty ``webhook_secret``.
        body: Raw request body (bytes).
        signature: Hex-encoded HMAC-SHA256 of ``body`` using the tenant
            secret. ``None`` or an empty string is rejected.

    Returns:
        Created PENDING :class:`DataEntryRecord`.

    Raises:
        InvalidSignature: if the signature is missing, malformed, or
            does not match the expected HMAC.
    """
    secret = tenant.webhook_secret.encode("utf-8") if tenant.webhook_secret else b""
    if not secret or not signature:
        raise InvalidSignature("missing or empty signature")
    expected = hmac.new(secret, body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise InvalidSignature("signature mismatch")
    payload = json.loads(body.decode("utf-8") or "{}")
    return DataEntryRecord.objects.create(
        tenant=tenant,
        source=DataEntryRecord.Source.WEBHOOK,
        raw=payload if isinstance(payload, dict) else {"value": payload},
    )
