"""Optional LangSmith free-tier tracing.

LangSmith is the only SaaS exception in the spec (free Developer tier).
This module flips the standard ``LANGCHAIN_TRACING_V2`` / ``LANGCHAIN_API_KEY``
env vars on when ``AI_ENABLE_LANGSMITH=1`` + a key are present, and leaves
them off otherwise. LangChain reads these vars at runtime, so no further
wiring is needed.
"""

import os

from ai_service.config import settings


def configure_langsmith() -> dict[str, object]:
    """Apply LangSmith env vars based on settings.

    Returns:
        A status dict suitable for ``/readyz``:
        ``{"enabled": bool, "reason": str}``.
    """
    if not settings.enable_langsmith:
        os.environ.pop("LANGCHAIN_TRACING_V2", None)
        os.environ.pop("LANGCHAIN_API_KEY", None)
        return {"enabled": False, "reason": "opt-in flag off"}
    if not settings.langsmith_api_key:
        os.environ.pop("LANGCHAIN_TRACING_V2", None)
        os.environ.pop("LANGCHAIN_API_KEY", None)
        return {"enabled": False, "reason": "missing AI_LANGSMITH_API_KEY"}
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = settings.langsmith_api_key
    return {"enabled": True, "reason": "free-tier tracing active"}
