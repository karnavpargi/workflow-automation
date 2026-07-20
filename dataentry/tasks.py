"""Validate -> map -> dispatch pipeline for staged dataentry records.

Each pipeline run is triggered by the Celery :func:`process_record`
task; the task is intentionally synchronous-friendly so tests can call
it directly. The pipeline is split into three small steps so each
failure mode is independently testable.

Status transitions:
    PENDING -> VALID -> DISPATCHED        (happy path)
    PENDING -> INVALID                    (validation failure)
"""

from celery import shared_task

from dataentry.models import DataEntryRecord

_REQUIRED_FIELDS: dict[str, tuple[str, ...]] = {
    "contact": ("name", "email"),
    "invoice": ("client_email", "number", "total", "due_date"),
    "other": (),
}


def _map(rec: DataEntryRecord) -> dict[str, object]:
    """Apply the tenant field map to ``rec.raw`` and return mapped fields.

    For now the field map is identity (raw == mapped); once tenants
    configure their own column-rename map, this is the only function
    that needs to change.
    """
    return dict(rec.raw)


def _validate(mapped: dict[str, object], target_type: str) -> None:
    """Raise ``ValueError`` if any required field for ``target_type`` is missing.

    Args:
        mapped: Normalized fields after :func:`_map`.
        target_type: One of the ``DataEntryRecord.target_type`` values.
    """
    required = _REQUIRED_FIELDS.get(target_type, ())
    missing = [f for f in required if not mapped.get(f)]
    if missing:
        raise ValueError(
            f"missing required field(s) for {target_type}: {', '.join(missing)}"
        )


def _dispatch(rec: DataEntryRecord) -> None:
    """Create the business object implied by ``rec.target_type``.

    * ``contact`` -> :class:`onboarding.models.Client`
    * ``invoice`` -> :class:`invoices.models.Invoice` (draft) + Client
    * ``other``   -> no-op
    """
    target = rec.target_type
    if target == "contact":
        from onboarding.models import Client

        Client.objects.create(
            tenant=rec.tenant,
            name=str(rec.mapped["name"]),
            email=str(rec.mapped["email"]),
        )
        return
    if target == "invoice":
        from datetime import date, datetime
        from decimal import Decimal

        from invoices.models import Invoice
        from onboarding.models import Client

        client, _ = Client.objects.get_or_create(
            tenant=rec.tenant,
            email=str(rec.mapped["client_email"]),
            defaults={"name": str(rec.mapped.get("client_name", ""))},
        )
        due_raw = rec.mapped["due_date"]
        due = (
            due_raw
            if isinstance(due_raw, date)
            else datetime.fromisoformat(str(due_raw)).date()
        )
        inv = Invoice(
            tenant=rec.tenant,
            client=client,
            number=str(rec.mapped["number"]),
            due_date=due,
            total=Decimal(str(rec.mapped["total"])),
        )
        inv._skip_total_recompute = True
        inv.save()
        return
    if target == "other":
        return
    raise ValueError(f"unknown target_type: {target}")


@shared_task
def process_record(record_id: int) -> str:
    """Validate, map, and dispatch a single staged record.

    Args:
        record_id: :class:`DataEntryRecord` PK.

    Returns:
        Final status string (``"dispatched"`` or ``"invalid"``).
    """
    rec = DataEntryRecord.objects.get(pk=record_id)
    try:
        mapped = _map(rec)
        _validate(mapped, rec.target_type)
        rec.mapped = mapped
        rec.status = DataEntryRecord.Status.VALID
        rec.save(update_fields=["mapped", "status"])
        _dispatch(rec)
        rec.status = DataEntryRecord.Status.DISPATCHED
        rec.save(update_fields=["status"])
        return rec.status
    except Exception as exc:  # noqa: BLE001
        rec.status = DataEntryRecord.Status.INVALID
        rec.error = str(exc)
        rec.save(update_fields=["status", "error"])
        return rec.status
