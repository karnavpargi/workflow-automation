"""Workflow handlers for the onboarding app.

The ``client.created`` handler is currently a no-op stub; Task 3 of Plan 4
replaces it with the real ``start_onboarding`` logic.
"""

from workflows import registry


def start_onboarding(event):  # noqa: ANN001
    """No-op stub for the client.created event.

    Args:
        event: The Event instance.
    """
    return None


registry.register("client.created", start_onboarding)
