"""Enable RLS on workflows_event and workflows_taskrecord."""

from django.db import migrations

from tenants.rls import enable_rls_on


class Migration(migrations.Migration):
    """Add RLS policies to workflows tables."""

    dependencies = [("workflows", "0001_initial")]

    operations = [
        migrations.RunPython(
            code=lambda apps, schema_editor: enable_rls_on("workflows_event"),
            reverse_code=lambda apps, schema_editor: None,
        ),
        migrations.RunPython(
            code=lambda apps, schema_editor: enable_rls_on("workflows_taskrecord"),
            reverse_code=lambda apps, schema_editor: None,
        ),
    ]
