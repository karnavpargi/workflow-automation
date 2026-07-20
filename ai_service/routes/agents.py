"""LangGraph agents wired as FastAPI routes.

Mounted under ``/agents`` in :mod:`ai_service.main`.
"""

import base64

from fastapi import APIRouter
from pydantic import BaseModel

from ai_service.agents import document_extract, email_parse

router = APIRouter()


class EmailParseRequest(BaseModel):
    """Request body for the email-parse agent."""

    raw: str


@router.post("/email-parse", status_code=201)
def email_parse_endpoint(body: EmailParseRequest) -> dict:
    """Parse ``body.raw`` into structured email fields.

    Args:
        body: Request payload.

    Returns:
        ``{"result": ..., "guard_reasons": [...]}``.
    """
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
def extract_document_endpoint(body: ExtractDocumentRequest) -> dict:
    """Parse, chunk, and ingest a document into pgvector.

    The actual embeddings are produced by the configured cascade
    (HuggingFace -> Ollama -> OpenAI). Returns the extracted text
    and the list of chunks written.
    """
    from ai_service.llm.embeddings import get_embeddings

    content = base64.b64decode(body.content_b64.encode("ascii"))
    text = document_extract.extract_text(content, body.content_type)
    chunks = document_extract.chunk_text(text)
    document_extract.ingest_chunks(
        tenant_id=0,  # placeholder: real impl threads tenant from JWT
        chunks=chunks,
        embeddings=get_embeddings(),
    )
    return {"text": text, "chunks": chunks}
