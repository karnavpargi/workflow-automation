"""Project package; imports Celery so shared tasks register."""
from wa_main.celery import app as celery_app  # noqa: F401

__all__ = ["celery_app"]
