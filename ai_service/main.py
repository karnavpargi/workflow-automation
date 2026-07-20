"""FastAPI AI service entrypoint.

Standalone microservice that runs alongside the Django app. Wired to
Ollama (free, self-hosted) and pgvector for embeddings; OpenAI /
LangSmith are opt-in via env flags.
"""

from fastapi import FastAPI

from ai_service.routes import agents, health, search

app = FastAPI(title="Workflow Automation AI Service", version="0.1.0")
app.include_router(health.router)
app.include_router(search.router, prefix="/search")
app.include_router(agents.router, prefix="/agents")
