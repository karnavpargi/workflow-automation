"""Data entry staging model.

A :class:`DataEntryRecord` is the single sink for every inbound data
source (form, CSV, XLSX, email, webhook). Each adapter creates a record
in ``PENDING`` state; the validate→map→dispatch pipeline (see
:mod:`dataentry.tasks`) moves it through ``VALID`` and ``DISPATCHED``,
or to ``INVALID`` / ``DEAD`` on terminal failure.
"""

from django.db import models


class DataEntryRecord(models.Model):
    """Staged inbound record awaiting validation and dispatch.

    Attributes:
        tenant: Owning tenant.
        source: Ingest channel (``form`` | ``csv`` | ``email`` | ``webhook``).
        status: Lifecycle (``pending`` | ``valid`` | ``invalid`` | ``dispatched``
            | ``dead``).
        raw: Original payload as ingested (pre-mapping).
        mapped: Normalized fields produced by the field-map step.
        target_type: What kind of business object to create on dispatch
            (``contact`` | ``invoice`` | ``other``).
        error: Last validation / dispatch error message, if any.
        created_at: Row creation timestamp.
    """

    class Source(models.TextChoices):
        """Ingest sources supported by the dataentry app."""

        FORM = "form", "Form"
        CSV = "csv", "CSV/Excel"
        EMAIL = "email", "Email"
        WEBHOOK = "webhook", "Webhook"

    class Status(models.TextChoices):
        """Record lifecycle.

        ``PENDING`` → ``VALID`` → ``DISPATCHED`` is the happy path.
        ``INVALID`` is reached when validation rejects the record; ``DEAD``
        is reserved for records that exhausted retries during dispatch.
        """

        PENDING = "pending", "Pending"
        VALID = "valid", "Valid"
        INVALID = "invalid", "Invalid"
        DISPATCHED = "dispatched", "Dispatched"
        DEAD = "dead", "Dead"

    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.CASCADE, related_name="dataentry_records"
    )
    source = models.CharField(max_length=20, choices=Source.choices)
    status = models.CharField(
        max_length=12, choices=Status.choices, default=Status.PENDING
    )
    raw = models.JSONField(default=dict)
    mapped = models.JSONField(default=dict)
    target_type = models.CharField(max_length=40, default="contact")
    error = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
