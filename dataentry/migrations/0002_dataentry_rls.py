"""Enable RLS on dataentry tables."""

from django.db import migrations

from tenants.rls import enable_rls_on


class Migration(migrations.Migration):
    """Add RLS policies to dataentry tables."""

    dependencies = [("dataentry", "0001_initial")]

    operations = [
        migrations.RunPython(
            code=lambda apps, schema_editor: enable_rls_on(
                "dataentry_dataentryrecord"
            ),
            reverse_code=lambda apps, schema_editor: None,
        ),
    ]
