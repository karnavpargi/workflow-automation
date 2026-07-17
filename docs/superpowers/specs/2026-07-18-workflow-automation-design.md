# Workflow Automation Platform — Design

**Date:** 2026-07-18
**Status:** Approved (pending user review of written spec)
**Author:** karnavpargi + opencode (brainstorming skill)

## Purpose

A multi-tenant SaaS platform that fully automates four classes of back-office
work for agencies and similar service businesses, sold both to the founding
agency (as an internal tool) and to external agencies (as a SaaS product).

Automation domains:

1. **Client onboarding** — new client created → welcome email, document
   collection request, account setup tasks fire automatically.
2. **Follow-ups** — reminders to clients/staff when a task, invoice, or
   milestone is due (email + internal task).
3. **Invoicing** — recurring and one-time invoice generation, PDF delivery,
   sync with Invoice Ninja, auto-reminders before due date.
4. **Data entry** — ingest from four sources: web forms, CSV/Excel uploads,
   inbound email parsing (LLM-assisted), inbound webhooks/API calls.
5. **AI assist** — LLM-driven email parsing, document extraction,
   follow-up drafting (RAG over past successes), semantic search across
   clients/invoices/audit log.

## Hard Constraints (apply to all implementation work)

- **PEP 8** strict compliance for all Python; enforced by `ruff` + `black`.
- **Google-style docstrings** on every module, class, method, and function;
  enforced by `pydocstyle` / `flake8-docstrings`.
- **ctx7** (`context7`) MUST be used for any library, framework, SDK, API, or
  CLI documentation lookup — Django, DRF, Celery, React, Vite, Invoice Ninja
  API, SuiteCRM API, Mattermost webhooks, **LangChain / LangGraph / LangSmith
  / pgvector / OpenAI / Ollama**, etc. Do not rely on memory.
- **`ui-ux-pro-max` skill** MUST be invoked before any React/UI component
  work — including admin-portal, client-portal, app-shell, ui-kit, and any
  surface that displays AI artifacts (drafted follow-ups, extracted data
  previews, agent trace viewers).
- **Fully self-hosted** — no managed/PaaS dependencies; everything runs as
  Docker services on a single VM, horizontally scalable later.
  **Exception:** LangSmith Developer (free SaaS tier, 5k traces/mo, 1 seat)
  is used for AI observability/eval/prompt hub only. All other infrastructure
  is self-hosted. Self-host LangSmith later if usage Enterprise-tier demands it.
- **Free / open-source integrations only** (LangSmith SaaS free tier is the
  sole commercial exception per above).
- **LLM providers:** OpenAI (primary) → Ollama (self-hosted backup), behind
  LangChain's `ChatModel` abstraction so swapping is one line.
- **LangChain ecosystem (all free OSS, MIT) is in scope:**
  `langchain`, `langchain-core`, `langchain-community`, `langchain-experimental`,
  `langgraph`, `langchain-postgres` (pgvector).
- **LangSmith (commercial SaaS, free Developer tier):** used for LLM tracing,
  evaluation, and Prompt Hub. Self-hosted Enterprise later when revenue permits.

## Architecture Overview

Multi-tenant SaaS workflow automation platform, fully self-hosted via Docker
Compose on a single VM (horizontally scalable later).

```
┌─────────────────────────────────────────────────────┐
│  Reverse Proxy (Caddy) — auto-TLS, routing             │
├─────────────────────────────────────────────────────┤
│  Frontend (React+Vite)  │  Backend API (Django+DRF)   │
├─────────────────────────────────────────────────────┤
│  Workers: Celery + Celery Beat (scheduled tasks)      │
├─────────────────────────────────────────────────────┤
│  Broker: Redis   │  DB: PostgreSQL   │  Obj storage: MinIO│
├─────────────────────────────────────────────────────┤
│  Integrations (sidecar services or HTTP clients):     │
│  • SuiteCRM · Invoice Ninja · Nextcloud · Mattermost  │
├─────────────────────────────────────────────────────┤
│  AI layer: LangGraph agents · OpenAI (primary) ·       │
│  Ollama (fallback) · pgvector on existing Postgres    │
├─────────────────────────────────────────────────────┤
│  AI service (FastAPI): agents + guards + audit · locust │
└─────────────────────────────────────────────────────┘
```

### Multi-tenancy

Single shared PostgreSQL database; rows scoped by `tenant_id` with Row-Level
Security (RLS) policies. Every tenant-scoped query goes through a
tenant-aware queryset; cross-tenant access returns 404 (no data leakage).

### Automation engine

- **Celery** — event-driven task queue. Django `transaction.on_commit`
  hooks fire tasks on model events (e.g. `client.created →
  onboarding.start`).
- **Celery Beat** — recurring schedules (recurring invoices, daily
  follow-up due checks).
- Every task carries an **idempotency key** (task name + entity id + step)
  so duplicate dequeues are no-ops.

## Technology Baseline

| Layer             | Technology                                              |
| ---------------- | ------------------------------------------------------- |
| Main backend     | Django + Django REST Framework (CRM, billing, tenants, workflows) |
| AI service       | FastAPI (separate Python microservice hosting LangGraph agents) |
| Language         | Python (PEP 8, Google docstrings)                       |
| Database         | PostgreSQL (self-hosted)                                |
| Cache / broker    | Redis (self-hosted)                                     |
| Task queue       | Celery + Celery Beat                                     |
| Auth             | `djangorestframework-simplejwt` + DRF permissions       |
| Email            | Django email backend + `django-anymail` (SMTP via Postfix) |
| Accounting       | Invoice Ninja (self-hosted)                             |
| CRM              | SuiteCRM (self-hosted)                                   |
| Documents        | Nextcloud (WebDAV) — Drive-style onboarding doc store  |
| Object storage   | MinIO (S3-compatible) — generated PDFs, attachments   |
| Frontend         | React (Vite) — `ui-ux-pro-max` skill for all UI work     |
| Frontend tests   | Vitest + React Testing Library; Playwright E2E          |
| Packaging        | Docker Compose (single VM); services decoupled for scale |
| Reverse proxy    | Caddy (auto-TLS)                                        |
| Chat             | Mattermost (self-hosted, webhook notifications)         |
| LLM provider     | OpenAI (primary) → Ollama (self-hosted fallback)        |
| AI framework     | LangChain + LangChain-Core + LangChain-Community + LangChain-Experimental |
| AI orchestration | LangGraph (stateful agents, HITL checkpoints)            |
| AI vector store  | pgvector extension on the same PostgreSQL (HNSW index)  |
| AI tracing/eval  | LangSmith Developer (free SaaS, 5k traces/mo, 1 seat)   |
| Document parsing | `unstructured` + `PyMuPDF` (pre-LLM text extraction)     |
| Embeddings       | OpenAI `text-embedding-3-small` → Ollama fallback → HuggingFace `BAAI/bge-small-en` (self-hosted last-resort) |
| Safety / RAI     | `guardrails-ai` + `presidio` (PII filter) + per-tenant rate limits + prompt-injection defense |
| Eval / EDA       | `pandas` + `scikit-learn` + `matplotlib` for offline eval dashboards on LangSmith exports |
| Load testing     | `locust` (Python, self-hosted, free)                     |

## Components (bounded units)

Each component has one clear purpose, a well-defined interface, and can be
understood and tested independently.

### Backend (Django apps)

- **`tenants/`** — Tenant model, membership, multi-tenancy middleware,
  RLS policy management.
- **`users/`** — User, RBAC (tenant admin / team member / client roles),
  JWT auth.
- **`audit/`** — append-only event log for compliance and debugging.
- **`workflows/`** — `Event`, `EventHandler`, `TaskRecord`; registry of
  workflow definitions.
- **`onboarding/`** — `OnboardingTemplate`, `OnboardingStep`; kicks off
  on `client.created`.
- **`followups/`** — `FollowupRule`, `Reminder`; scheduled via Celery Beat.
- **`invoices/`** — `Invoice`, `LineItem`, `RecurringSchedule`; syncs to
  Invoice Ninja.
- **`dataentry/`** — `SourceAdapter` (Form/CSV/Email/Webhook), `Parser`,
  `Record` staging queue.
- **`integrations/`** — Adapter pattern:
  - `CrmAdapter` (SuiteCRM REST)
  - `BillingAdapter` (Invoice Ninja REST)
  - `StorageAdapter` (Nextcloud WebDAV / MinIO S3)
  - `ChatAdapter` (Mattermost webhooks)
  - `EmailAdapter` (Django email + `django-anymail` SMTP)
- **`notifications/`** — Outbox, channels (email/chat), templating.
- **`ai/llm/`** — provider factory (`ChatOpenAI` → `ChatOllama` fallback),
  model registry, per-tenant model config, token budget tracking.
  All calls traced via `langchain.callbacks` to LangSmith.
- **`ai/embeddings/`** — `EmbeddingsOpenAI(text-embedding-3-small)` → Ollama
  embedding fallback; service used for semantic search and RAG ingest.
- **`ai/agents/`** — LangGraph agent definitions, one per use case:
  - `EmailParsingAgent` — parse → classify → extract structured fields →
    dispatch to `dataentry` (replaces the regex-only parser branch)
  - `DocumentExtractionAgent` — `unstructured` pre-parse → LLM structured
    extraction → pgvector embed for semantic search
  - `FollowupDraftingAgent` — RAG over tenant's past successful follow-ups
    (pgvector) → draft reminder copy (HITL checkpoint before send)
- **`ai/prompts/`** — versioned prompt registry synced from LangSmith Prompt
  Hub; pins prompt versions per release so evals are reproducible.
- **`ai/extraction/`** — thin wrapper over `unstructured` + `PyMuPDF` for
  pre-LLM text extraction (PDFs, DOCX, XLSX, EML).
- **`ai/safety/`** — `guardrails-ai` input/output guards, `presidio` PII
  scrub, prompt-injection classifier, moderation adapter (OpenAI moderation
  → local fallback), and the `ai_llm_call` audit writer.
- **`ai/eval/`** — `pandas` + `scikit-learn` + `matplotlib` notebooks /
  scripts that pull LangSmith exports and produce offline eval dashboards
  (F1 for extraction, ROC-AUC for the injection classifier, helpfulness).

### AI service (FastAPI microservice)

A separate Python service — `ai_service/` — built with **FastAPI**,
containerized alongside Django. It owns all LangGraph agents and LLM I/O so
LLM concerns never leak into the Django monolith.

- **Routes:**
  - `POST /agents/email-parse` — run `EmailParsingAgent` on a raw email.
  - `POST /agents/extract-document` — run `DocumentExtractionAgent` on an uploaded doc.
  - `POST /agents/draft-followup` — run `FollowupDraftingAgent` with context; returns draft + guard decisions + trace URL.
  - `POST /search` — pgvector semantic search across the tenant's corpus.
- **Every route** applies the input guards → agent → output guards → audit, and returns a stable JSON envelope `{data, guards, trace_url, cost_usd, latency_ms}`.
- **Auth** — shared JWT verification with Django (same secret, same claims, tenant_id enforced in every query).
- **Health** — `/healthz` for liveness, `/readyz` checks OpenAI + Ollama + pgvector connectivity.

**Layering convention:**

- `models.py` — data shape only (no business logic).
- `services.py` — business logic; the public interface other apps call.
- `views.py` / `serializers.py` — thin HTTP wrappers over `services.py`.
- Integration adapters expose a stable interface (e.g. `BillingAdapter.push(invoice)`)
  and hide vendor-specific HTTP details, so vendors can be swapped per tenant.

### Frontend (React + Vite)

- **`app-shell/`** — routing, auth, tenant context, role guards.
- **`admin-portal/`** — agency workflows, workflow viewer, audit log,
  tenant configuration.
- **`client-portal/`** — invoices due, onboarding status, documents.
- **`ui-kit/`** — shared components; built with the `ui-ux-pro-max` skill.

### Workers

- **Celery worker** — event handlers, retries, idempotency.
- **Celery Beat** — recurring schedules (recurring invoices, follow-up
  due checks).

## Data Flow

### Flow A — New client onboarding (fully automated)

```
[Admin UI: create client]
   → POST /api/clients (Django view, thin)
   → clients.services.create_client() commits row;
     transaction.on_commit fires:
       → Celery task: onboarding.start(tenant_id, client_id)
   → OnboardingTemplate resolves steps for tenant
   → For each step: queue a delayed Celery task
     (welcome email, doc request upload link from Nextcloud,
      kickoff call placeholder)
   → notifications.send_email() renders template,
     passes to django-anymail SMTP
   → audit.log(...) records each step
   → Client portal: status visible in real-time
```

### Flow B — Recurring invoice

```
[Celery Beat: daily 00:00]
   → check_recurring_invoices() scans invoices due today per tenant
   → invoices.services.issue_invoice() builds PDF
   → BillingAdapter.push(invoice) → Invoice Ninja (REST)
   → EmailAdapter.send() → client email with PDF attached
   → followups.schedule() → auto-reminder 7 days before due
   → Mattermost webhook("Invoice issued: …")
   → audit.log(...)
```

### Flow C — Data entry (email parsing, LLM-assisted)

```
[Inbound email] → POST /api/dataentry/webhook (oauth'd mailbox)
   → ai.extraction.unstructured.parse() — raw text + structure pre-LLM
   → ai.agents.EmailParsingAgent (LangGraph) runs:
       parse → classify (contact / invoice / support / unknown)
              → extract structured fields via LLM tool-calling
              → dispatch to dataentry.services.ingest_record()
   → Stages Record in `dataentry_record` with status="pending"
   → Celery task: validate → map → dispatch
     (creates Contact / Invoice / whatever target type field says)
   → Failure → retry queue (3x) → dead-letter → audit + Mattermost alert
   → LangSmith traces every LLM call (cost + latency + quality)
```

### Flow D — Follow-up drafting (RAG + HITL)

```
[followups.schedule() fires] → Celery task: draft_followup(tenant, context)
   → pgvector: retrieve top-k past successful follow-ups for this tenant/category
   → ai.agents.FollowupDraftingAgent (LangGraph):
       system prompt (versioned in LangSmith Prompt Hub)
         + retrieved examples
         + context (client name, amount, due date)
       → drafts reminder copy
   → HITL checkpoint: draft queued in admin-portal "Review queue"
   → Tenant admin approves/edits → notifications.send_email()
   → After send: outcome (+click/reply metadata later) stored as RAG positive
     example for future drafts
```

Each flow has a clear trigger, an idempotent worker, a retry policy, an
audit record, and observable state.

## Error Handling

Layered, typed, and never worker-crashing.

- **Validation errors (400)** — serializers raise
  `serializers.ValidationError`; views return structured JSON
  `{errors: [{field, message}]}`.
- **Auth errors (401/403)** — simplejwt + DRF permission classes.
- **Not found (404)** — tenant-scoped querysets auto-filter, so
  cross-tenant access returns 404 (no data leakage).
- **Workflow / task errors** —
  - Celery tasks wrapped as:
    `@celery_app.task(bind=True, autoretry_for=(RetryableError,), max_retries=3)`
  - Exponential backoff: 60s → 5 min → 30 min.
  - Dead-letter: after retries exhausted →
    `TaskRecord.status="dead"` + Mattermost alert + audit log.
  - Idempotency: every task carries
    `idempotency_key = (task_name, entity_id, step)`;
    duplicate dequeues are no-ops.
- **Integration errors** — Adapters raise typed exceptions
  (`IntegrationUnavailable`, `IntegrationAuthFailed`,
  `IntegrationRateLimited`); each maps to a retry policy.
- **Tenant data isolation** — Row-Level Security policies on every
  tenant-scoped table; tests assert cross-tenant access fails.

## Responsible AI (guardrails, auditability, user outcomes)

Every LLM call in the system passes through a guardrail layer in the FastAPI
AI service before it is sent to OpenAI/Ollama, and every response is filtered
and logged before it reaches a user or downstream workflow.

- **Input guards (`Guardrails-AI`)** — applied at the FastAPI boundary:
  - Prompt-injection detection (known-injection patterns + a small classifier).
  - PII detection via `presidio-analyzer` (email, phone, SSN, card, IBAN)
    with redaction or rejection per tenant policy.
  - Topic restriction: tenant-configurable allow-list of categories the
  LLM is permitted to discuss (e.g. "invoice, onboarding, follow-ups"); out-of-scope → reject + audit.
  - Token/prompt-size cap per request.
- **Output guards** — applied before returning the LLM result:
  - `presidio` PII scrub on model output.
  - Schema-constrained generation via LangChain `with_structured_output` so
  agents cannot return free-form payloads to downstream services.
  - Content classifier: reject hate/harassment/self-harm (OpenAI
  moderation endpoint; Ollama fallback uses a small local classifier).
- **Auditability** — every LLM I/O record stored in `ai_llm_call`:
  tenant_id, user_id, agent_name, prompt_version, input_hash, output_hash,
  guard_decisions, latency_ms, cost_usd, langsmith_trace_url. Retained 180 days.
- **Per-tenant rate limits + budgets** — tokens-per-day and
  requests-per-minute per tenant; overage → queue (not fail).
- **HITL checkpoints** — any LLM output that becomes an outbound message
  (follow-up draft, onboarding copy) stops in a Review Queue; a human
  admin approves/edits before send.
- **Prompt versioning** — prompts pinned per release via LangSmith Prompt
  Hub; rollback is a config flip, no code dep.
- **Continuous eval** — LangSmith Evals run nightly over a held-out
  evaluation set per agent (email-classification accuracy, field-extraction
  F1, follow-up helpfulness score). Regressions open a Mattermost alert.
- **User-outcome feedback loop** — outcome of approved follow-ups
  (replied/paid/ignored) feeds the RAG corpus and the eval set, so the
  system measurably improves over time.

## Testing Strategy (TDD throughout)

Discipline: tests before implementation, per the `test-driven-development`
skill. Red → Green → Refactor. No implementation code without a failing test.

- **Unit tests** — `pytest` + `pytest-django`; behavioral tests for every
  `services.py` function; boundary cases; no DB where avoidable.
- **Integration tests** — Django `APIClient` against a real DB; assert
  outcomes, not implementation.
- **Adapter tests** — each integration adapter tested against a mocked
  HTTP service (`responses` or `httpx_mock`); a `MAKE_REAL=1` env var
  unlocks live tests against local Dockerized SuiteCRM/Invoice Ninja.
- **Workflow tests** — Celery in eager mode (`task_always_eager`) for
  deterministic event → task → state assertions.
- **Multi-tenancy tests** — a parametrized "cross-tenant access returns
  404 / cannot read other tenant's data" test per app.
- **Frontend tests** — Vitest + React Testing Library for components;
  Playwright E2E for the two portal critical paths:
  1. Login → onboarding status (admin),
  2. Login → pay invoice (client).
- **AI agent tests** — each LangGraph agent pinned with golden I/O cases
  in a fixtures file (so offline tests don't burn tokens); live-LLM tests
  run only when `MAKE_REAL=1` and assert schema validity, guard decisions,
  and that PII is scrubbed. Stochastic assertions use scikit-learn metrics
  (F1 for field extraction, ROC-AUC for the injection classifier).
- **Locust load tests** — per FastAPI AI endpoint: target p95 < 4s for a
  typical follow-up draft, < 2s for email classification. Tenants stay
  within configured tokens/min. Run nightly in CI.
- **Eval suite** — LangSmith Evals run nightly; regression threshold gates
  the model-promote gate.
- **Coverage** — target ≥ 85% on `services.py` layers; monitored in CI.

## CI Guardrails

All checks must pass before merge.

- `ruff` + `black` (PEP 8 + formatting).
- `pydocstyle` / `flake8-docstrings` (Google docstrings).
- `mypy` (strict on `services/` and `integrations/`; optional elsewhere).
- Frontend: `eslint` + `prettier`.
- `pytest` + `vitest` + Playwright smoke.

## Out of Scope

- Marketplace / sales of the SaaS to outside agencies beyond multi-tenancy
  plumbing (no billing for the SaaS itself yet).
- Mobile native apps (responsive web only for v1).
- Custom model training (PyTorch/TensorFlow/SageMaker/Azure ML pipelines).
  We use off-the-shelf OpenAI/Ollama models + LangChain; no fine-tuning in v1.
- Managed cloud platforms (AWS Fargate/ECS, Azure AKS, SageMaker, Bedrock).
- Any managed/PaaS dependency (Supabase, Render, Railway, Fly.io).