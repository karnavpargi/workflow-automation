"""Seed a load-test tenant + admin user for Locust runs.

Usage:
    DJANGO_SETTINGS_MODULE=wa_main.settings.dev \\
        python ops/locust/seed_load_user.py
"""

import os

import django


def main() -> None:
    """Create a load-test tenant + user if they don't exist yet."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wa_main.settings.dev")
    django.setup()

    from django.contrib.auth import get_user_model

    from tenants import services as tsvc

    User = get_user_model()
    tenant, _ = tsvc.create_tenant(name="Load Test", slug="load")
    user, created = User.objects.get_or_create(
        email="load@test.io",
        defaults={"username": "load"},
    )
    if created:
        user.set_password("load")
        user.save()
        print(f"created user load@test.io (tenant={tenant.slug})")
    else:
        print(f"user load@test.io already exists (tenant={tenant.slug})")


if __name__ == "__main__":
    main()
