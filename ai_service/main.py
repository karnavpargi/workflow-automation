"""FastAPI AI service entrypoint.

Standalone microservice that runs alongside the Django app. Wired to
Ollama (free, self-hosted) and pgvector for embeddings; OpenAI /
LangSmith are opt-in via env flags. The ``/metrics`` endpoint is
optional — it's mounted only when ``prometheus-fastapi-instrumentator``
is installed (the free OSS path, brought in by ``pip install -e .[ops]``).
"""

from fastapi import FastAPI

from ai_service.routes import agents, health, search

app = FastAPI(title="Workflow Automation AI Service", version="0.1.0")
app.include_router(health.router)
app.include_router(search.router, prefix="/search")
app.include_router(agents.router, prefix="/agents")

# Optional Prometheus instrumentation (free OSS).
try:
    from prometheus_fastapi_instrumentator import Instrumentator

    Instrumentator().instrument(app).expose(app)
except ImportError:  # pragma: no cover - optional dep
    pass
