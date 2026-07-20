"""Non-LLM email ingest adapter.

Uses the free ``mail-parser`` library to extract From / Subject / Body
from a raw ``.eml`` payload. Plan 9 will replace this with the LLM
parser; until then we keep the extracted fields as-is.
"""

import mailparser

from dataentry.models import DataEntryRecord


def _first_address(value: object) -> str:
    """Return the bare email address from a ``mail-parser`` From tuple.

    ``mail-parser`` returns ``[(name, address), ...]``; we just want the
    first address (the From sender).
    """
    if not value:
        return ""
    first = value[0]
    if isinstance(first, (list, tuple)) and len(first) >= 2:
        return str(first[1] or "")
    return str(first)


def ingest_email(tenant, eml_bytes: bytes) -> DataEntryRecord:
    """Ingest a raw ``.eml`` payload.

    Args:
        tenant: Owning tenant.
        eml_bytes: Raw email as bytes.

    Returns:
        Created PENDING :class:`DataEntryRecord` whose ``raw`` contains
        ``from``, ``subject``, and ``body`` keys.
    """
    msg = mailparser.parse_from_bytes(eml_bytes)
    return DataEntryRecord.objects.create(
        tenant=tenant,
        source=DataEntryRecord.Source.EMAIL,
        raw={
            "from": _first_address(msg.from_),
            "subject": msg.subject or "",
            "body": msg.body or "",
        },
    )
