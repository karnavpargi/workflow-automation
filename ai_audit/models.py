"""LLM call audit model.

Every agent invocation in the AI service emits one row here via the
internal ingest endpoint. The table is append-only at the DB level
(matching the existing ``audit`` app) so an attacker with DB write
access cannot rewrite call history.
"""

from django.db import models


class LlmCall(models.Model):
    """Immutable record of one LLM invocation.

    Attributes:
        tenant: Owning tenant.
        user_id: Acting user id if known (extracted from JWT).
        agent_name: Agent that made the call (e.g. ``email_parse``).
        prompt_version: Prompt pin id.
        input_hash: SHA256 of the (redacted) input.
        output_hash: SHA256 of the (redacted) output.
        guard_decisions: JSON list of guard results.
        latency_ms: End-to-end latency.
        cost_usd: Estimated cost (0 for Ollama).
        langsmith_trace_url: Optional free-tier trace URL.
        created_at: Timestamp.
    """

    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.CASCADE, related_name="llm_calls"
    )
    user_id = models.IntegerField(null=True, blank=True)
    agent_name = models.CharField(max_length=100)
    prompt_version = models.CharField(max_length=50, default="v1")
    input_hash = models.CharField(max_length=64)
    output_hash = models.CharField(max_length=64)
    guard_decisions = models.JSONField(default=list)
    latency_ms = models.IntegerField(default=0)
    cost_usd = models.DecimalField(max_digits=10, decimal_places=6, default=0)
    langsmith_trace_url = models.URLField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """LlmCall model metadata."""

        indexes = [models.Index(fields=["tenant", "agent_name", "created_at"])]
