"""Celery application factory for the workflow-automation project."""
import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wa_main.settings.dev")

app = Celery("wa_main")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
