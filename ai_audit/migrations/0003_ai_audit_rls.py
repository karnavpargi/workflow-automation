"""Enable RLS on ai_audit tables."""

from django.db import migrations

from tenants.rls import enable_rls_on


class Migration(migrations.Migration):
    """Add RLS policies to ai_audit tables."""

    dependencies = [("ai_audit", "0002_llmcall_append_only")]

    operations = [
        migrations.RunPython(
            code=lambda apps, schema_editor: enable_rls_on("ai_audit_llmcall"),
            reverse_code=lambda apps, schema_editor: None,
        ),
    ]
