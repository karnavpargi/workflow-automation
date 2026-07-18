"""WSGI entrypoint."""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wa_main.settings.dev")
application = get_wsgi_application()
