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
   inbound email parsing, inbound webhooks/API calls.

## Hard Constraints (apply to all implementation work)

- **PEP 8** strict compliance for all Python; enforced by `ruff` + `black`.
- **Google-style docstrings** on every module, class, method, and function;
  enforced by `pydocstyle` / `flake8-docstrings`.
- **ctx7** (`context7`) MUST be used for any library, framework, SDK, API, or
  CLI documentation lookup — Django, DRF, Celery, React, Vite, Invoice Ninja
  API, SuiteCRM API, Mattermost webhooks, etc. Do not rely on memory.
- **`ui-ux-pro-max` skill** MUST be invoked before any React/UI component
  work (app-shell, admin-portal, client-portal, ui-kit).
- **Fully self-hosted** — no managed/PaaS dependencies; everything runs as
  Docker services on a single VM, horizontally scalable later.
- **Free / open-source integrations only.**

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
| Backend          | Django + Django REST Framework                          |
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

### Flow C — Data entry (email parsing)

```
[Inbound email] → POST /api/dataentry/webhook (oauth'd mailbox)
   → DataEntryAdapter.parse() — mail-parser lib for structure extraction
   → Stages Record in `dataentry_record` with status="pending"
   → Celery task: validate → map → dispatch
     (creates Contact / Invoice / whatever target type field says)
   → Failure → retry queue (3x) → dead-letter → audit + Mattermost alert
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
- AI / LLM-driven workflow generation (rule/event-driven only for v1).
- Any managed/PaaS dependency (Supabase, Render, Railway, Fly.io).