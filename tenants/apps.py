"""App config for tenants."""

from django.apps import AppConfig


class TenantsConfig(AppConfig):
    """Hold configuration for the tenants app.

    Attributes:
        default_auto_field: DB field type for auto primary keys.
        name: Dotted path of the app.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "tenants"
