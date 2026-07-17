# Load Testing + Eval Ops Implementation Plan (Plan 11 of 11)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Locust load tests for Django + FastAPI AI endpoints, nightly offline eval job, cost/latency/quality dashboards from free tools, and operational runbooks.

**Architecture:** `ops/locust/` for load profiles. `ops/eval/` for nightly golden-set eval. Metrics via free Prometheus + Grafana (optional compose profile) or simple CSV + matplotlib from Plan 9 harness. Alerts to Mattermost (free).

**Tech Stack (free/OSS only):** locust, pytest, pandas, scikit-learn, matplotlib, optional prometheus/grafana free images, Mattermost webhooks.

**Depends on:** Plans 1–10.

---

## Free/OSS hard rules

- Locust is free.
- No Datadog / New Relic / paid APM.
- Optional Prometheus + Grafana free OSS images only.
- Mattermost for alerts (already in stack).

---

## File Structure

```
ops/
├── locust/
│   ├── locustfile.py
│   ├── users_admin.py
│   └── users_ai.py
├── eval/
│   ├── run_nightly.py
│   └── thresholds.yaml
├── dashboards/
│   └── README.md          # how to import free Grafana dashboards
├── runbooks/
│   ├── incident.md
│   └── scaling.md
docker-compose.ops.yml     # optional prometheus + grafana
.github/workflows/nightly.yml
```

---

### Task 1: Locust profiles

```python
# ops/locust/locustfile.py
"""Locust load profiles for API and AI service."""
from locust import HttpUser, between, task


class AdminUser(HttpUser):
    """Simulates an agency admin hitting core APIs."""

    wait_time = between(1, 3)
    host = "http://localhost:8000"

    def on_start(self) -> None:
        """Login and store token.

        Raises:
            RuntimeError: if login fails.
        """
        r = self.client.post(
            "/api/auth/token/",
            json={"email": "load@test.io", "password": "load"},
            headers={"X-Tenant-Slug": "load"},
        )
        if r.status_code != 200:
            raise RuntimeError("login failed")
        self.token = r.json()["access"]
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "X-Tenant-Slug": "load",
        }

    @task(3)
    def list_clients(self) -> None:
        """GET clients list."""
        self.client.get("/api/clients/", headers=self.headers)

    @task(1)
    def create_client(self) -> None:
        """POST a new client (onboarding)."""
        self.client.post(
            "/api/clients/",
            json={"name": "Load Client", "email": "c@load.io"},
            headers=self.headers,
        )


class AiUser(HttpUser):
    """Simulates AI agent calls."""

    wait_time = between(2, 5)
    host = "http://localhost:8001"

    @task
    def email_parse(self) -> None:
        """POST /agents/email-parse with a sample body."""
        self.client.post(
            "/agents/email-parse",
            json={"raw": "From: a@b.com\nSubject: Invoice\n\nPlease pay $100"},
            headers={"Authorization": "Bearer test"},
        )
```

- [ ] Document targets from spec: p95 email-parse < 2s, draft-followup < 4s
- [ ] Seed script for load-test tenant/user
- [ ] Commit: `feat(ops): Locust profiles for API + AI`

---

### Task 2: Nightly eval job

```yaml
# .github/workflows/nightly.yml
name: Nightly eval
on:
  schedule: [{ cron: "0 3 * * *" }]
  workflow_dispatch:

jobs:
  eval:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install -e ".[dev]"
      - run: python ops/eval/run_nightly.py
      - name: Fail on regression
        run: test -f ops/eval/last_ok
```

```python
# ops/eval/run_nightly.py
"""Run golden-set eval and enforce thresholds."""
from pathlib import Path

import yaml

from ai_service.eval.harness import eval_email_parse


def main() -> None:
    """Load thresholds, run eval, write last_ok marker if green.

    Raises:
        SystemExit: on regression below thresholds.
    """
    thresholds = yaml.safe_load(Path("ops/eval/thresholds.yaml").read_text())
    # predictions would come from recorded or live (MAKE_REAL) run
    predictions = [{"category": "invoice"}]  # replaced by real runner
    metrics = eval_email_parse(
        Path("ai_service/eval/golden/email_parse.jsonl"), predictions
    )
    if metrics["macro_f1"] < thresholds["email_parse_macro_f1"]:
        raise SystemExit(f"regression: {metrics}")
    Path("ops/eval/last_ok").write_text("ok\n")


if __name__ == "__main__":
    main()
```

```yaml
# ops/eval/thresholds.yaml
email_parse_macro_f1: 0.80
```

- [ ] Commit: `feat(ops): nightly eval workflow + thresholds`

---

### Task 3: Optional free metrics stack

- [ ] `docker-compose.ops.yml` with free images:
  - `prom/prometheus`
  - `grafana/grafana-oss`
- [ ] Instrument FastAPI with free `prometheus-fastapi-instrumentator`
- [ ] Instrument Django with free `django-prometheus`
- [ ] Mattermost alert webhook on threshold breach
- [ ] Commit: `feat(ops): optional Prometheus/Grafana OSS profile`

---

### Task 4: Runbooks

- [ ] `ops/runbooks/incident.md` — LLM down (Ollama restart), DB full, Redis OOM, dead tasks
- [ ] `ops/runbooks/scaling.md` — scale workers, scale ai_service replicas, pgvector index tips
- [ ] Commit: `docs(ops): incident + scaling runbooks`

---

### Task 5: Final green gate

- [ ] Full `docker compose up` smoke
- [ ] `pytest && npm test && locust --headless -u 10 -r 2 -t 1m`
- [ ] Document default free path in root README
- [ ] Commit: `docs: free/OSS default path README + final smoke checklist`

---

## Self-Review

- Spec load tests, eval, cost/latency/quality monitoring covered with free tools.
- No paid APM.
- Closes the 11-plan series.
