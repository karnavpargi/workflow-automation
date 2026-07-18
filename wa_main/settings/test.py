"""Test settings: in-memory-ish Postgres via env, eager Celery."""

import os

from wa_main.settings.base import *  # noqa: F401,F403

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
# Tests use a dedicated DB; pytest-django creates/destroys it.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME", "wa_test"),
        "USER": os.environ.get("DB_USER", "wa"),
        "PASSWORD": os.environ.get("DB_PASSWORD", "wa"),
        "HOST": os.environ.get("DB_HOST", "localhost"),
        "PORT": os.environ.get("DB_PORT", "5432"),
    }
}
