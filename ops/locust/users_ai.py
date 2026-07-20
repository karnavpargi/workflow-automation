"""AI service user class for Locust load tests.

Simulates AI agent calls against the FastAPI service. Auth uses a
``Bearer`` placeholder token; real auth requires a Django-issued JWT
(``plan 10 frontend``). The test exercises latency on the agent
endpoints under sustained load.

Spec targets (per ``ops/runbooks/scaling.md``):
  * p95 ``/agents/email-parse`` < 2s
  * p95 ``/agents/draft-followup`` < 4s
"""

from locust import HttpUser, between, task

_SAMPLE_EMAIL = (
    "From: lead@example.com\n"
    "Subject: Quote request\n"
    "\n"
    "Please send me a quote for 5 licenses, due Friday. Thanks!\n"
)


class AiUser(HttpUser):
    """Simulates AI agent calls against the FastAPI service."""

    wait_time = between(2, 5)
    host = "http://localhost:8001"

    @task(3)
    def email_parse(self) -> None:
        """POST /agents/email-parse with a sample body."""
        self.client.post(
            "/agents/email-parse",
            json={"raw": _SAMPLE_EMAIL},
            headers={"Authorization": "Bearer load-test-token"},
        )

    @task(1)
    def draft_followup(self) -> None:
        """POST /agents/draft-followup (slowest endpoint; target p95 < 4s)."""
        self.client.post(
            "/agents/draft-followup",
            json={
                "tenant_id": 1,
                "invoice_number": "INV-LOAD-1",
                "due_date": "2026-12-31",
                "recipient_email": "x@y.io",
            },
            headers={"Authorization": "Bearer load-test-token"},
        )
