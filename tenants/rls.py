"""Raw SQL helpers for tenant Row-Level Security (RLS).

We enable RLS on every tenant-scoped table and enforce
``tenant_id = current_setting('app.tenant_id')``. The application sets
the session variable per request (via a small helper added in Task 9)
so even a buggy queryset cannot leak another tenant's rows.
"""

from django.db import connection

TENANT_SCOPED_TABLES = [
    "tenants_tenant",
    "audit_auditlog",
    "workflows_event",
    "workflows_taskrecord",
    "onboarding_client",
    "onboarding_onboardingtemplate",
    "onboarding_onboardingrun",
]


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


def disable_rls_on(table: str) -> None:
    """Disable RLS on ``table`` and drop the policy.

    Used in test setup so most tests can create tenants without setting
    ``app.tenant_id``. The 2 RLS-specific tests re-enable RLS locally
    via :func:`enable_rls_on` to exercise the policy.

    Args:
        table: The PostgreSQL table name (schema-qualified allowed).
    """
    sql = f"""
    ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;
    DROP POLICY IF EXISTS tenant_isolation ON {table};
    """
    with connection.cursor() as cur:
        cur.execute(sql)


def set_session_tenant(tenant_id: int) -> None:
    """Set the current request's tenant id on the DB connection.

    Uses ``SET`` (not ``SET LOCAL``) so the GUC applies whether the
    caller is inside a transaction or not. Tests run as
    ``TransactionTestCase`` for the cross-tenant RLS assertion
    because the test needs to issue DDL between INSERTs and SELECTs;
    in that mode there is no wrapping transaction for ``SET LOCAL``
    to attach to.

    Args:
        tenant_id: The active tenant's PK.
    """
    with connection.cursor() as cur:
        cur.execute("SET app.tenant_id = %s", [str(tenant_id)])


def reset_session_tenant() -> None:
    """Clear the tenant id (used in tests between cases)."""
    with connection.cursor() as cur:
        cur.execute("RESET app.tenant_id")
