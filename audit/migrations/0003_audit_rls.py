"""Enable RLS on audit_auditlog so it follows the same isolation rule."""

from django.db import migrations

from tenants.rls import enable_rls_on


class Migration(migrations.Migration):
    """Add RLS policy to audit_auditlog."""

    dependencies = [("audit", "0002_append_only")]

    operations = [
        migrations.RunPython(
            code=lambda apps, schema_editor: enable_rls_on("audit_auditlog"),
            reverse_code=lambda apps, schema_editor: None,
        ),
    ]
