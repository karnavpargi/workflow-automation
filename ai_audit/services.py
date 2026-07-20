"""Public service for recording LLM calls.

Wraps ``LlmCall.objects.create`` so callers never have to import the
model directly; mirrors :mod:`audit.services`.
"""

from ai_audit.models import LlmCall


def record_llm_call(
    *,
    tenant,
    agent_name: str,
    input_hash: str,
    output_hash: str,
    guard_decisions: list | None = None,
    user_id: int | None = None,
    prompt_version: str = "v1",
    latency_ms: int = 0,
    cost_usd: float = 0,
    langsmith_trace_url: str = "",
) -> LlmCall:
    """Append an LLM call row.

    Args:
        tenant: Owning tenant.
        agent_name: Name of the agent that made the call.
        input_hash: SHA256 of the (redacted) input.
        output_hash: SHA256 of the (redacted) output.
        guard_decisions: Optional list of guard result strings.
        user_id: Acting user id if known.
        prompt_version: Prompt pin id (default ``v1``).
        latency_ms: End-to-end latency.
        cost_usd: Estimated cost (0 for free/local models).
        langsmith_trace_url: Optional free-tier trace URL.

    Returns:
        The created :class:`LlmCall`.
    """
    return LlmCall.objects.create(
        tenant=tenant,
        agent_name=agent_name,
        input_hash=input_hash,
        output_hash=output_hash,
        guard_decisions=guard_decisions or [],
        user_id=user_id,
        prompt_version=prompt_version,
        latency_ms=latency_ms,
        cost_usd=cost_usd,
        langsmith_trace_url=langsmith_trace_url,
    )
