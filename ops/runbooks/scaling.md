# Scaling Runbook

Free/OSS first. Each tier is a copy-pasteable `docker compose`
override. No paid services.

## Tier 0: single-host (current dev)

- 1× `web`, 1× `worker`, 1× `beat`, 1× `ai_service`, 1× `ollama`.
- 100s of req/s. Sufficient for the MVP and small-team tenants.

## Tier 1: scale Celery horizontally

- `docker compose up -d --scale worker=4` (4 worker replicas).
- The Beat container stays at 1 (only one Beat leader should run).
- Tune `worker_concurrency` via env if needed.

## Tier 2: scale the AI service

- `docker compose up -d --scale ai_service=3` (3 replicas).
- Ollama is the bottleneck; one Ollama per 3-5 AI service replicas
  is a reasonable rule of thumb. Either:
  - co-locate Ollama on the same host and rely on TCP; or
  - run a small Ollama cluster (Ollama supports multi-GPU).
- pgvector is read-heavy; for 1M+ chunks, add an `ivfflat` or `hnsw`
  index. Migration example:

  ```sql
  CREATE INDEX ON langchain_pg_embedding USING hnsw (embedding vector_cosine_ops);
  ```

- Rate limiter (Plan 9 `ai_service/limits.py`) is Redis-backed, so
  it works across replicas without changes.

## Tier 3: scale Postgres

- Move from the in-stack Postgres to a managed-free option like
  [Postgres.ai](https://www.postgres.ai/) (free tier), or a self-
  hosted cluster with `pg_auto_failover`.
- Add read replicas for analytics queries; the RLS policy still
  applies per connection.

## pgvector index tips

- `hnsw` is faster to build, slower to update; use for read-mostly
  corpora.
- `ivfflat` is faster to update, slower to query; use when chunks
  are added frequently.
- Always set `lists` ≥ `sqrt(rows)` for `ivfflat`.
- The migration in `audit/migrations/0003_audit_rls.py` is the
  template for adding an RLS-protected pgvector table.

## Vertical scaling quick wins

- Ollama on a GPU host: pull a larger model, raise `OLLAMA_NUM_PARALLEL`.
- Django workers: set `WEB_CONCURRENCY` to 2 × CPU.
- AI service: set `uvicorn --workers 2` for multi-core hosts.

## Cost (free/OSS path) summary

| Component | Free/OSS | Capacity tier |
|---|---|---|
| Postgres + pgvector | self-hosted | tier 0-3 |
| Redis | self-hosted | tier 0-3 |
| Ollama | self-hosted (free) | tier 0-2 |
| HuggingFace embeddings | free/local | tier 0-3 |
| OpenAI | opt-in (paid) | tier 3+ |
| LangSmith | opt-in (free dev tier) | tier 3+ |
| Prometheus | free/OSS | tier 0-3 |
| Grafana OSS | free/OSS | tier 0-3 |
| Mattermost | self-hosted (free) | tier 0-3 |
