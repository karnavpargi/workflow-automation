# AI Agents + Responsible AI Implementation Plan (Plan 9 of 11)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship LangGraph agents (email parse, document extraction, follow-up drafting with RAG + HITL), Responsible AI guardrails (free tools), PII scrub (Presidio free), audit of every LLM I/O, and offline eval harness (pandas/scikit-learn free).

**Architecture:** Agents live in `ai_service/agents/`. Safety in `ai_service/safety/`. Django stores `ai_llm_call` audit rows via internal webhook from AI service. HITL review queue in Django `followups` (draft status). All models free by default (Ollama + HF).

**Tech Stack (free/OSS):** LangGraph, unstructured, PyMuPDF, guardrails-ai (free OSS), presidio-analyzer + presidio-anonymizer (MIT), pandas, scikit-learn, matplotlib. No paid APIs required.

**Depends on:** Plans 6–8.

---

## Free/OSS hard rules

- Default models = Ollama + HF embeddings.
- `guardrails-ai` open-source validators; OpenAI moderation endpoint is **opt-in only**.
- Presidio is fully free/self-hosted.
- No paid vector DB.

---

## File Structure

```
ai_service/
├── agents/
│   ├── email_parse.py
│   ├── document_extract.py
│   └── followup_draft.py
├── safety/
│   ├── input_guards.py
│   ├── output_guards.py
│   └── pii.py
├── eval/
│   ├── harness.py
│   └── golden/
│       ├── email_parse.jsonl
│       └── extract.jsonl
├── routes/agents.py          # wire real handlers
django apps:
  ai_audit/                   # ai_llm_call model + internal ingest endpoint
  followups/                  # extend Reminder with draft status for HITL
```

---

### Task 1: PII scrub (Presidio free)

```python
# ai_service/safety/pii.py
"""PII detection and redaction via Microsoft Presidio (MIT, free)."""
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

_analyzer = AnalyzerEngine()
_anonymizer = AnonymizerEngine()


def redact_pii(text: str) -> str:
    """Redact PII entities from text.

    Args:
        text: Input text.

    Returns:
        Text with PII replaced by placeholders.
    """
    results = _analyzer.analyze(text=text, language="en")
    return _anonymizer.anonymize(text=text, analyzer_results=results).text


def contains_pii(text: str) -> bool:
    """Return True if PII entities are detected.

    Args:
        text: Input text.

    Returns:
        Detection flag.
    """
    return bool(_analyzer.analyze(text=text, language="en"))
```

- [ ] Tests with sample emails/phones + commit: `feat(ai): Presidio PII scrub`

---

### Task 2: Input / output guards (guardrails-ai free)

```python
# ai_service/safety/input_guards.py
"""Input guardrails for LLM prompts."""
from ai_service.safety.pii import contains_pii, redact_pii

INJECTION_PATTERNS = (
    "ignore previous instructions",
    "system prompt",
    "jailbreak",
    "disregard all",
)


class GuardDecision:
    """Result of a guard check.

    Attributes:
        allowed: Whether the request may proceed.
        reasons: List of rejection reasons.
        sanitized_text: Possibly redacted text.
    """

    def __init__(self, allowed: bool, reasons: list[str], sanitized_text: str) -> None:
        """Store decision fields.

        Args:
            allowed: Pass/fail.
            reasons: Rejection reasons.
            sanitized_text: Cleaned text.
        """
        self.allowed = allowed
        self.reasons = reasons
        self.sanitized_text = sanitized_text


def check_input(text: str, *, redact: bool = True) -> GuardDecision:
    """Run input guards.

    Args:
        text: Raw user/system input.
        redact: If True, PII is redacted rather than rejected.

    Returns:
        GuardDecision.
    """
    reasons: list[str] = []
    lowered = text.lower()
    for pat in INJECTION_PATTERNS:
        if pat in lowered:
            reasons.append(f"injection:{pat}")
    sanitized = redact_pii(text) if redact else text
    if not redact and contains_pii(text):
        reasons.append("pii_detected")
    if len(text) > 20_000:
        reasons.append("too_long")
    return GuardDecision(allowed=not reasons, reasons=reasons, sanitized_text=sanitized)
```

```python
# ai_service/safety/output_guards.py
"""Output guardrails for LLM responses."""
from ai_service.safety.pii import redact_pii


def check_output(text: str) -> str:
    """Scrub PII from model output.

    Args:
        text: Raw model output.

    Returns:
        Scrubbed text.
    """
    return redact_pii(text)
```

- [ ] Tests + commit: `feat(ai): input/output guards (injection + PII + length)`

---

### Task 3: EmailParsingAgent (LangGraph)

```python
# ai_service/agents/email_parse.py
"""LangGraph agent: parse → classify → extract structured fields."""
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph
from pydantic import BaseModel, Field

from ai_service.llm.factory import get_chat_model
from ai_service.safety.input_guards import check_input
from ai_service.safety.output_guards import check_output


class EmailFields(BaseModel):
    """Structured fields extracted from an email.

    Attributes:
        category: contact | invoice | support | unknown.
        name: Sender name if present.
        email: Sender email if present.
        amount: Invoice amount if present.
        summary: One-line summary.
    """

    category: str = Field(description="contact|invoice|support|unknown")
    name: str = ""
    email: str = ""
    amount: str = ""
    summary: str = ""


class EmailState(TypedDict):
    """Graph state for email parsing."""

    raw: str
    sanitized: str
    result: dict[str, Any]
    guard_reasons: list[str]


def _guard(state: EmailState) -> EmailState:
    """Apply input guards.

    Args:
        state: Graph state.

    Returns:
        Updated state.
    """
    decision = check_input(state["raw"])
    return {
        **state,
        "sanitized": decision.sanitized_text,
        "guard_reasons": decision.reasons,
        "result": {} if decision.allowed else {"category": "unknown"},
    }


def _extract(state: EmailState) -> EmailState:
    """Run structured extraction via LLM.

    Args:
        state: Graph state.

    Returns:
        Updated state with result.
    """
    if state["guard_reasons"]:
        return state
    llm = get_chat_model().with_structured_output(EmailFields)
    fields: EmailFields = llm.invoke(
        "Extract fields from this email:\n" + state["sanitized"]
    )
    cleaned = check_output(fields.model_dump_json())
    return {**state, "result": EmailFields.model_validate_json(cleaned).model_dump()}


def build_email_parse_graph():
    """Compile the email parse graph.

    Returns:
        Compiled LangGraph app.
    """
    g = StateGraph(EmailState)
    g.add_node("guard", _guard)
    g.add_node("extract", _extract)
    g.set_entry_point("guard")
    g.add_edge("guard", "extract")
    g.add_edge("extract", END)
    return g.compile()
```

- [ ] Golden I/O fixtures (no live LLM in CI): mock `get_chat_model`
- [ ] Live test gated by `MAKE_REAL=1`
- [ ] Wire `POST /agents/email-parse`
- [ ] Commit: `feat(ai): EmailParsingAgent (LangGraph)`

---

### Task 4: DocumentExtractionAgent

- [ ] Pre-parse with free `unstructured` + `PyMuPDF`
- [ ] LLM structured extraction (schema-constrained)
- [ ] Embed chunks into pgvector for semantic search
- [ ] Wire `POST /agents/extract-document`
- [ ] Tests + commit: `feat(ai): DocumentExtractionAgent + pgvector ingest`

---

### Task 5: FollowupDraftingAgent (RAG + HITL)

- [ ] Retrieve top-k past successful follow-ups from pgvector (tenant-scoped)
- [ ] Draft via Ollama with system prompt from local prompt file (not LangSmith unless opted in)
- [ ] Return draft; do **not** send
- [ ] Django endpoint stores draft as Reminder with status=`draft`
- [ ] Admin approves → existing `process_due` / send path
- [ ] On successful outcome later, re-embed as positive RAG example
- [ ] Commit: `feat(ai): FollowupDraftingAgent RAG + HITL draft queue`

---

### Task 6: LLM call audit (Django)

```python
# ai_audit/models.py
"""Append-only LLM call audit."""
from django.db import models


class LlmCall(models.Model):
    """One LLM invocation record for auditability.

    Attributes:
        tenant: Owning tenant.
        user_id: Acting user id if known.
        agent_name: Agent that made the call.
        prompt_version: Prompt pin id.
        input_hash: SHA256 of input.
        output_hash: SHA256 of output.
        guard_decisions: JSON list of guard results.
        latency_ms: End-to-end latency.
        cost_usd: Estimated cost (0 for Ollama).
        langsmith_trace_url: Optional free-tier trace URL.
        created_at: Timestamp.
    """

    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE)
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
```

- [ ] Internal ingest endpoint (service token) called by AI service after every call
- [ ] Append-only trigger (same as audit app)
- [ ] Tests + commit: `feat(ai): LlmCall audit model + ingest`

---

### Task 7: Offline eval harness (pandas + sklearn free)

```python
# ai_service/eval/harness.py
"""Offline eval over golden fixtures and optional LangSmith exports."""
import json
from pathlib import Path

import pandas as pd
from sklearn.metrics import f1_score


def eval_email_parse(golden_path: Path, predictions: list[dict]) -> dict:
    """Compute classification F1 against golden labels.

    Args:
        golden_path: JSONL of {raw, category}.
        predictions: List of {category} aligned with golden.

    Returns:
        Metrics dict with macro_f1.
    """
    gold = [json.loads(line)["category"] for line in golden_path.read_text().splitlines()]
    pred = [p["category"] for p in predictions]
    return {"macro_f1": float(f1_score(gold, pred, average="macro"))}
```

- [ ] Golden fixtures checked into repo
- [ ] CI job runs offline eval (mocked LLM or recorded outputs)
- [ ] Commit: `feat(ai): offline eval harness (pandas/sklearn)`

---

### Task 8: Rate limits + budgets per tenant

- [ ] Redis token bucket in AI service (free Redis already in stack)
- [ ] Config: requests/min + tokens/day per tenant
- [ ] Over limit → HTTP 429, not hard fail of worker
- [ ] Commit: `feat(ai): per-tenant rate limits via Redis`

---

## Self-Review

- Spec AI use cases + Responsible AI section covered.
- Free/OSS path complete without any API key.
- OpenAI moderation / LangSmith remain opt-in only.
