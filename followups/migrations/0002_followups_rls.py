"""Enable RLS on followups tables."""

from django.db import migrations

from tenants.rls import enable_rls_on


class Migration(migrations.Migration):
    """Add RLS policies to followups tables."""

    dependencies = [("followups", "0001_initial")]

    operations = [
        migrations.RunPython(
            code=lambda apps, schema_editor: enable_rls_on("followups_followuprule"),
            reverse_code=lambda apps, schema_editor: None,
        ),
        migrations.RunPython(
            code=lambda apps, schema_editor: enable_rls_on("followups_reminder"),
            reverse_code=lambda apps, schema_editor: None,
        ),
    ]
