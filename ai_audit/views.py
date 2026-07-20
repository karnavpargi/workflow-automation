"""Internal ingest endpoint for the AI service to record LLM calls.

Auth is a shared service token carried in ``X-AI-Service-Token``;
the value is ``settings.AI_AUDIT_SERVICE_TOKEN`` (env: ``AI_AUDIT_SERVICE_TOKEN``).
This endpoint is intended only for the AI microservice, not the public
Django API.
"""

import hashlib
import os

from rest_framework import status
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from ai_audit.services import record_llm_call


def _service_token() -> str:
    """Return the expected service token from the environment."""
    return os.environ.get("AI_AUDIT_SERVICE_TOKEN", "")


def _hash(text: str) -> str:
    """SHA256 hex digest of ``text`` (used to redact payloads)."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def ingest_llm_call(request):
    """Record one LLM call. Requires the shared service token.

    Request body:
        ``tenant_slug``, ``agent_name``, ``input_text``, ``output_text``,
        optional ``user_id``, ``prompt_version``, ``latency_ms``,
        ``cost_usd``, ``langsmith_trace_url``, ``guard_decisions``.

    Returns:
        201 on success, 401 on bad token, 400 on bad payload.
    """
    expected = _service_token()
    presented = request.META.get("HTTP_X_AI_SERVICE_TOKEN", "")
    if not expected or presented != expected:
        return Response(
            {"error": "invalid service token"}, status=status.HTTP_401_UNAUTHORIZED
        )

    data = request.data
    tenant_slug = data.get("tenant_slug")
    agent_name = data.get("agent_name")
    input_text = data.get("input_text", "")
    output_text = data.get("output_text", "")
    if not tenant_slug or not agent_name:
        return Response(
            {"error": "tenant_slug and agent_name are required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    from tenants.models import Tenant

    try:
        tenant = Tenant.objects.get(slug=tenant_slug)
    except Tenant.DoesNotExist:
        return Response({"error": "unknown tenant"}, status=status.HTTP_404_NOT_FOUND)

    record_llm_call(
        tenant=tenant,
        agent_name=str(agent_name),
        input_hash=_hash(str(input_text)),
        output_hash=_hash(str(output_text)),
        guard_decisions=list(data.get("guard_decisions", []) or []),
        user_id=data.get("user_id"),
        prompt_version=str(data.get("prompt_version", "v1")),
        latency_ms=int(data.get("latency_ms", 0) or 0),
        cost_usd=float(data.get("cost_usd", 0) or 0),
        langsmith_trace_url=str(data.get("langsmith_trace_url", "") or ""),
    )
    return Response({"status": "ok"}, status=status.HTTP_201_CREATED)
