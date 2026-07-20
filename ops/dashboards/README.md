"""Optional Prometheus + Grafana OSS profile (free only).

Bring up alongside the main stack to scrape FastAPI + Django metrics:

    docker compose -f docker-compose.yml -f docker-compose.ops.yml up -d

The Grafana dashboard JSONs in ``ops/dashboards/`` are imported by
pointing Grafana at that folder. They are the free OSS community
dashboards for the FastAPI Instrumentator + django-prometheus exporters.
"""

# In this environment we don't actually run docker, so this file is a
# declarative contract checked in. A real deployment would:
# 1. `docker compose -f docker-compose.yml -f docker-compose.ops.yml up -d`
# 2. open Grafana on :3000, import the dashboards under ops/dashboards/
# 3. point Prometheus at the `ai_service` and `web` containers
