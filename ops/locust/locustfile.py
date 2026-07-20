"""Locust entry point.

Imports every user class so ``locust -f ops/locust/locustfile.py``
discovers them all. Run with one of the targets below:

    # API load test
    locust -f ops/locust/locustfile.py AdminUser --host http://localhost:8000

    # AI service load test
    locust -f ops/locust/locustfile.py AiUser --host http://localhost:8001

    # CI headless smoke
    locust -f ops/locust/locustfile.py -u 10 -r 2 -t 30s --headless
"""

from ops.locust.users_admin import AdminUser
from ops.locust.users_ai import AiUser

__all__ = ["AdminUser", "AiUser"]
