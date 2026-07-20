"""LangGraph agents wired as FastAPI routes.

Mounted under ``/agents`` in :mod:`ai_service.main`.
"""

from fastapi import APIRouter
from pydantic import BaseModel

from ai_service.agents import email_parse

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
