"""Form ingest adapter.

Trivial passthrough: store the submitted fields verbatim in
``DataEntryRecord.raw`` and return the new PENDING record.
"""

from dataentry.models import DataEntryRecord


def ingest_form(tenant, fields: dict) -> DataEntryRecord:
    """Create a PENDING ``DataEntryRecord`` from a form submission.

    Args:
        tenant: Owning tenant.
        fields: Raw form field values keyed by field name.

    Returns:
        Created :class:`DataEntryRecord`.
    """
    return DataEntryRecord.objects.create(
        tenant=tenant,
        source=DataEntryRecord.Source.FORM,
        raw=dict(fields),
    )
