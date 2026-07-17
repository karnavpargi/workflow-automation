"""Raw SQL helpers for tenant Row-Level Security (RLS).

We enable RLS on every tenant-scoped table and enforce
``tenant_id = current_setting('app.tenant_id')``. The application sets
the session variable per request (via a small helper added in Task 9)
so even a buggy queryset cannot leak another tenant's rows.
"""

from django.db import connection

TENANT_SCOPED_TABLES = ["tenants_tenant", "audit_auditlog"]


def enable_rls_on(table: str) -> None:
    """Enable RLS and create a restrictive policy on ``table``.

    Args:
        table: The PostgreSQL table name (schema-qualified allowed).
    """
    sql = f"""
    ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;
    ALTER TABLE {table} FORCE ROW LEVEL SECURITY;
    CREATE POLICY tenant_isolation ON {table}
        USING (tenant_id::text = current_setting('app.tenant_id', true));
    """
    with connection.cursor() as cur:
        cur.execute(sql)


def set_session_tenant(tenant_id: int) -> None:
    """Set the current request's tenant id on the DB connection.

    Args:
        tenant_id: The active tenant's PK.
    """
    with connection.cursor() as cur:
        cur.execute("SET LOCAL app.tenant_id = %s", [str(tenant_id)])


def reset_session_tenant() -> None:
    """Clear the tenant id (used in tests between cases)."""
    with connection.cursor() as cur:
        cur.execute("RESET app.tenant_id")
