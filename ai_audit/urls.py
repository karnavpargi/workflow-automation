"""URL routes for the ai_audit app."""

from django.urls import path

from ai_audit.views import ingest_llm_call

urlpatterns = [
    path("llm-calls/", ingest_llm_call, name="ai-audit-ingest"),
]
