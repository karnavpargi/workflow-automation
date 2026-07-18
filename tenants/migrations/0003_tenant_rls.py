"""Enable tenant_id column + RLS on tenants_tenant and define the policy.

The ``tenant_id`` column is a STORED generated column that mirrors ``id``,
so each tenant's own row has ``tenant_id = id``. This makes the RLS policy
``tenant_id = current_setting('app.tenant_id')`` work even for the
tenants table itself: a tenant can always see its own row and only its
own row.
"""
from django.db import migrations

from tenants.rls import enable_rls_on


class Migration(migrations.Migration):
    """Add tenant_id (generated) and RLS policy to tenants_tenant."""

    dependencies = [("tenants", "0002_initial")]

    operations = [
        migrations.RunSQL(
            sql=(
                "ALTER TABLE tenants_tenant "
                "ADD COLUMN IF NOT EXISTS tenant_id INT "
                "GENERATED ALWAYS AS (id) STORED"
            ),
            reverse_sql=(
                "ALTER TABLE tenants_tenant DROP COLUMN IF EXISTS tenant_id"
            ),
        ),
        migrations.RunPython(
            code=lambda apps, schema_editor: enable_rls_on("tenants_tenant"),
            reverse_code=lambda apps, schema_editor: None,
        ),
    ]
