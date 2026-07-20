"""Enable RLS on followups_successfulfollowup."""

from django.db import migrations

from tenants.rls import enable_rls_on


class Migration(migrations.Migration):
    """Add RLS policy to followups_successfulfollowup."""

    dependencies = [("followups", "0004_successfulfollowup")]

    operations = [
        migrations.RunPython(
            code=lambda apps, schema_editor: enable_rls_on(
                "followups_successfulfollowup"
            ),
            reverse_code=lambda apps, schema_editor: None,
        ),
    ]
