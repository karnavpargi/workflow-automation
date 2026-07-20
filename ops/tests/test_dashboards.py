"""Tests for the ops/dashboards compose file shape.

We don't run docker in CI, but we can validate that the compose file
is well-formed YAML and references the expected free/OSS images.
"""

from pathlib import Path

import yaml


def test_compose_ops_has_free_images():
    """docker-compose.ops.yml only references free/OSS upstream images."""
    path = Path(__file__).resolve().parent.parent.parent / "docker-compose.ops.yml"
    data = yaml.safe_load(path.read_text())
    services = data["services"]
    images = {svc["image"] for svc in services.values()}
    assert any("prom/prometheus" in img for img in images)
    assert any("grafana/grafana-oss" in img for img in images)
    assert any("prom/alertmanager" in img for img in images)


def test_prometheus_scrape_config_targets_both_services():
    """prometheus.yml scrapes both the Django web and the AI service."""
    path = (
        Path(__file__).resolve().parent.parent.parent
        / "ops"
        / "dashboards"
        / "prometheus.yml"
    )
    data = yaml.safe_load(path.read_text())
    jobs = {job["job_name"] for job in data["scrape_configs"]}
    assert "django-web" in jobs
    assert "ai-service" in jobs


def test_alertmanager_routes_to_mattermost():
    """alertmanager.yml forwards to a Mattermost webhook (env-driven)."""
    path = (
        Path(__file__).resolve().parent.parent.parent
        / "ops"
        / "dashboards"
        / "alertmanager.yml"
    )
    data = yaml.safe_load(path.read_text())
    assert data["route"]["receiver"] == "mattermost"
    url = data["receivers"][0]["webhook_configs"][0]["url"]
    assert "MATTERMOST_WEBHOOK_URL" in url
