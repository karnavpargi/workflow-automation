"""Enable RLS on invoices tables."""

from django.db import migrations

from tenants.rls import enable_rls_on


class Migration(migrations.Migration):
    """Add RLS policies to invoices tables."""

    dependencies = [("invoices", "0001_initial")]

    operations = [
        migrations.RunPython(
            code=lambda apps, schema_editor: enable_rls_on("invoices_invoice"),
            reverse_code=lambda apps, schema_editor: None,
        ),
        migrations.RunPython(
            code=lambda apps, schema_editor: enable_rls_on(
                "invoices_recurringschedule"
            ),
            reverse_code=lambda apps, schema_editor: None,
        ),
    ]
