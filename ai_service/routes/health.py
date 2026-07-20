"""Health routes for the AI service.

Two endpoints:
  * ``/healthz`` is a liveness probe (no I/O).
  * ``/readyz`` is a readiness probe that checks Ollama + pgvector.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/healthz")
def healthz() -> dict[str, str]:
    """Liveness probe.

    Returns:
        Static OK status.
    """
    return {"status": "ok"}


@router.get("/readyz")
def readyz() -> dict[str, object]:
    """Readiness probe: checks Ollama + pgvector reachability.

    Returns:
        Status dict plus per-dependency flags.
    """
    from ai_service.db import pgvector_reachable
    from ai_service.llm.factory import ollama_reachable

    return {
        "status": "ok",
        "ollama": ollama_reachable(),
        "pgvector": pgvector_reachable(),
    }
