"""Enable RLS on onboarding tables that carry a ``tenant_id`` column.

The fourth onboarding table, ``onboarding_onboardingstep``, is intentionally
left without RLS: it has no ``tenant_id`` column of its own (steps are
owned transitively through ``template``), and the policy helper
:func:`tenants.rls.enable_rls_on` requires a direct ``tenant_id`` column.
Cross-tenant access to steps is still prevented at the ORM layer because
the only access path is ``template.steps.all()`` and the template is
RLS-protected.
"""
from django.db import migrations

from tenants.rls import enable_rls_on


class Migration(migrations.Migration):
    """Add RLS policies to onboarding tables with a ``tenant_id`` column."""

    dependencies = [("onboarding", "0001_initial")]

    operations = [
        migrations.RunPython(
            code=lambda apps, schema_editor: enable_rls_on("onboarding_client"),
            reverse_code=lambda apps, schema_editor: None,
        ),
        migrations.RunPython(
            code=lambda apps, schema_editor: enable_rls_on("onboarding_onboardingtemplate"),
            reverse_code=lambda apps, schema_editor: None,
        ),
        migrations.RunPython(
            code=lambda apps, schema_editor: enable_rls_on("onboarding_onboardingrun"),
            reverse_code=lambda apps, schema_editor: None,
        ),
    ]
