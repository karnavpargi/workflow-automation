"""App config for users."""
from django.apps import AppConfig


class UsersConfig(AppConfig):
    """Hold configuration for the users app.

    Attributes:
        default_auto_field: DB field type for auto primary keys.
        name: Dotted path of the app.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "users"
