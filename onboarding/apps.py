"""App config for onboarding.

Registers the client.created event handler in ``ready()``. The real
handler logic (Task 3 of Plan 4) replaces the no-op stub here.
"""

from django.apps import AppConfig


class OnboardingConfig(AppConfig):
    """App config for onboarding."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "onboarding"

    def ready(self) -> None:
        """Register workflow handlers.

        The no-op stub for ``client.created`` is replaced in Task 3 with
        the real ``start_onboarding`` handler.
        """
        from onboarding import handlers  # noqa: F401  -- registers handlers
        from workflows import registry
        from workflows.exceptions import HandlerNotFound

        if not registry.get("client.created"):
            # Should never happen if onboarding/handlers.py is imported.
            raise HandlerNotFound("client.created")
