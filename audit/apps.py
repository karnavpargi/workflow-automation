"""App config for audit."""
from django.apps import AppConfig


class AuditConfig(AppConfig):
    """Hold configuration for the audit app.

    Attributes:
        default_auto_field: DB field type for auto primary keys.
        name: Dotted path of the app.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "audit"
