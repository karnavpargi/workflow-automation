# Incident Response Runbook

Free/OSS stack only. Steps assume a `docker compose` deployment.

## LLM down (Ollama unreachable)

**Symptom:** `/ai/readyz` returns `ollama: false`; agents time out.

1. Check the Ollama container: `docker compose ps ollama`.
2. Check the model is loaded: `docker compose exec ollama ollama list`.
3. If the container is healthy but the model is missing, pull it:
   `docker compose exec ollama ollama pull llama3.1`.
4. If Ollama is OOM-killed, check `docker compose logs ollama` and
   raise the memory limit; or pin to a smaller model
   (`qwen2.5:0.5b`).
5. As a fallback, the AI service automatically falls back to
   `HuggingFaceEmbeddings` for embeddings; for chat it raises
   `RuntimeError("No LLM provider available")` and agents return
   503 to callers.

## Postgres disk full

**Symptom:** migrations fail; insert errors.

1. `docker compose exec db vacuumdb -U wa -d wa -z` (reclaim space).
2. Check for runaway audit rows: `SELECT COUNT(*) FROM audit_auditlog;`.
3. If the `ai_audit_llmcall` table is the culprit, the append-only
   trigger blocks `DELETE`; either archive rows with `pg_dump` then
   `TRUNCATE` (which bypasses row triggers on `DELETE` but is a
   DDL-level operation) or rotate with a partitioning migration.
4. Resize the volume or attach a larger EBS-equivalent.

## Redis OOM

**Symptom:** Celery raises `ConnectionError`; rate limiter (Plan 9)
returns 500s.

1. `docker compose ps redis` — check the OOMKill counter.
2. `docker compose exec redis redis-cli INFO memory`.
3. If Celery's result backend is the culprit, switch to a smaller
   result expiration (`CELERY_RESULT_EXPIRES=300`).
4. If the rate limiter is filling keys fast, lower the per-tenant
   limit (Plan 9 settings).

## Dead tasks (Celery Beat)

**Symptom:** `audit_log` shows `workflow.task.dead` events; reminders
or invoices stop firing.

1. `docker compose logs worker` — look for the exception that caused
   `DEAD` after `MAX_RETRIES=4` (Plans 2, 5, 6 set this).
2. `docker compose exec web python manage.py shell` →
   `from workflows.models import TaskRecord; TaskRecord.objects.filter(status="dead").values()`
3. For each dead task: either
   - mark `pending` again to retry: `t.status="pending"; t.save()`
   - or cancel: `t.status="cancelled"; t.save()`
4. If the underlying vendor (MinIO / Invoice Ninja / Mattermost) is
   down, restart the vendor container and the task will retry on
   the next Beat tick (manual re-queue recommended to avoid waiting).

## Cross-tenant leak suspected

**Symptom:** a row from another tenant appears in a query.

1. **Do not** try to `UPDATE`/`DELETE` on the table — the RLS
   trigger blocks it (Plan 6 followups + ai_audit).
2. `docker compose exec db psql -U wa -d wa` and run
   `SELECT current_setting('app.tenant_id', true);` to see the
   active GUC.
3. Check `tenants/rls.py` to confirm the table is in
   `TENANT_SCOPED_TABLES`.
4. If the table is missing, add it + a migration to enable RLS
   (template: `audit/migrations/0003_audit_rls.py`).

## Secrets rotation

1. `DJANGO_SECRET_KEY` rotation: edit `.env`, restart `web worker beat`.
2. `AI_JWT_SECRET` rotation: must match Django's `SECRET_KEY` for
   cross-service JWTs to keep verifying. Rotate both together.
3. `AI_AUDIT_SERVICE_TOKEN`: pick a new token, set on both the AI
   service and any caller; restart the AI service.
