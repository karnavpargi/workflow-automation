"""LangGraph agents wired as FastAPI routes.

Mounted under ``/agents`` in :mod:`ai_service.main`. All endpoints
require a valid JWT (verified by :func:`ai_service.auth.current_user`)
and use the ``tenant_id`` claim rather than a request body field —
the body ``tenant_id`` on ``/agents/draft-followup`` is preserved for
backward compatibility but the agent ignores it.
"""

import base64

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ai_service.agents import document_extract, email_parse
from ai_service.auth import current_user

router = APIRouter()


class EmailParseRequest(BaseModel):
    """Request body for the email-parse agent."""

    raw: str


@router.post("/email-parse", status_code=201)
def email_parse_endpoint(
    body: EmailParseRequest,
    claims: dict = Depends(current_user),  # noqa: B008
) -> dict:
    """Parse ``body.raw`` into structured email fields.

    Args:
        body: Request payload.
        claims: Decoded JWT claims (provides ``user_id`` + ``tenant_id``).

    Returns:
        ``{"result": ..., "guard_reasons": [...]}``.
    """
    _ = claims  # auth-only; tenant scoping is upstream of the agent itself
    graph = email_parse.build_email_parse_graph()
    out = graph.invoke({"raw": body.raw})
    return {
        "result": out.get("result", {}),
        "guard_reasons": out.get("guard_reasons", []),
    }


class ExtractDocumentRequest(BaseModel):
    """Request body for the document-extract agent.

    ``content_b64`` carries base64-encoded file bytes; ``content_type``
    selects the partitioner (PDF, plain text, HTML, etc.).
    """

    content_b64: str
    content_type: str = "text/plain"


@router.post("/extract-document", status_code=201)
def extract_document_endpoint(
    body: ExtractDocumentRequest,
    claims: dict = Depends(current_user),  # noqa: B008
) -> dict:
    """Parse, chunk, and ingest a document into pgvector.

    The actual embeddings are produced by the configured cascade
    (HuggingFace -> Ollama -> OpenAI). The pgvector collection is
    scoped to the JWT's ``tenant_id`` so each tenant's chunks are
    isolated.

    Returns:
        The extracted text and the list of chunks written.
    """
    from ai_service.llm.embeddings import get_embeddings

    tenant_id = int(claims["tenant_id"])
    content = base64.b64decode(body.content_b64.encode("ascii"))
    text = document_extract.extract_text(content, body.content_type)
    chunks = document_extract.chunk_text(text)
    document_extract.ingest_chunks(
        tenant_id=tenant_id,
        chunks=chunks,
        embeddings=get_embeddings(),
    )
    return {"text": text, "chunks": chunks}


class DraftFollowupRequest(BaseModel):
    """Request body for the followup-draft agent.

    ``tenant_id`` in the body is **deprecated** — the JWT claim
    ``tenant_id`` is authoritative. The body field is kept for
    backward compatibility but the agent ignores it.
    """

    tenant_id: int | None = None
    invoice_number: str
    due_date: str
    recipient_email: str


@router.post("/draft-followup", status_code=201)
def draft_followup_endpoint(
    body: DraftFollowupRequest,
    claims: dict = Depends(current_user),  # noqa: B008
) -> dict:
    """Generate a follow-up draft and persist it as a DRAFT Reminder.

    The Reminder is created in the JWT's ``tenant_id`` — the body's
    ``tenant_id`` is ignored. This is the multi-tenancy contract.

    Args:
        body: Request payload.
        claims: Decoded JWT claims.

    Returns:
        ``{"reminder_id": int, "draft_text": str}``.
    """
    if "tenant_id" not in claims:
        raise HTTPException(status_code=400, detail="missing tenant_id in token")
    from ai_service.agents import followup_draft

    return followup_draft.draft_followup(
        tenant_id=int(claims["tenant_id"]),
        invoice_number=body.invoice_number,
        due_date_iso=body.due_date,
        recipient_email=body.recipient_email,
    )
