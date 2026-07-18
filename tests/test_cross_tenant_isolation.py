"""Cross-tenant isolation contract; every future tenant-scoped model must
pass this same shape. This first test pins the audit table, which is
already tenant-scoped, as the reference."""

from collections.abc import Generator

import pytest
from django.db import connection

from tenants.rls import enable_rls_on, reset_session_tenant, set_session_tenant


@pytest.fixture(autouse=True)
def _restore_rls_state() -> Generator[None, None, None]:
    """Make sure RLS is off for both tenant-scoped tables around this test.

    The session-scoped ``django_db_setup`` disables RLS so the 14
    non-RLS tests can create tenant rows without setting the GUC.
    The RLS test in this module manually re-enables RLS on
    ``audit_auditlog`` between its data setup and its assertion;
    this fixture guarantees the next test in the session starts with
    RLS disabled again on both tenant-scoped tables.
    """
    with connection.cursor() as cur:
        for table in ("tenants_tenant", "audit_auditlog"):
            cur.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
            cur.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")
    yield
    with connection.cursor() as cur:
        for table in ("tenants_tenant", "audit_auditlog"):
            cur.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
            cur.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")


@pytest.mark.django_db(transaction=True)
def test_rls_blocks_cross_tenant_audit_rows() -> None:
    """Setting a session tenant and querying audit rows only returns own.

    Marked ``transaction=True`` because :func:`enable_rls_on` issues
    DDL (``ALTER TABLE``) and PostgreSQL refuses to run DDL while the
    current transaction holds pending trigger events from the
    append-only ``audit_auditlog`` triggers. The transaction marker
    drops the per-test savepoint so each statement (including the
    DDL) is its own micro-transaction.
    """
    from audit import services
    from tenants import services as tsvc
    from users.models import User

    # Step 1: set up data with RLS off (session fixture ensures this).
    ua = User.objects.create_user(email="a@x.io", password="p", username="a")
    ub = User.objects.create_user(email="b@x.io", password="p", username="b")
    ta = tsvc.create_tenant(name="A", slug="a", admin=ua)
    tb = tsvc.create_tenant(name="B", slug="b", admin=ub)
    services.log(tenant=ta, actor=ua, event="x")
    services.log(tenant=tb, actor=ub, event="x")
    # Step 2: re-enable RLS so the policy actually applies to the SELECT.
    enable_rls_on("audit_auditlog")
    # Step 3: set the GUC and verify only own rows are visible.
    try:
        set_session_tenant(ta.id)
        with connection.cursor() as cur:
            cur.execute("SELECT tenant_id FROM audit_auditlog")
            rows = [r[0] for r in cur.fetchall()]
        # The RLS contract: no rows from other tenants are visible.
        # create_tenant() also writes an audit row, so there will be
        # >=1 row for ta; the important property is that none of
        # them belong to tb.
        assert rows, "expected at least one audit row for tenant A"
        assert all(r == ta.id for r in rows), rows
        assert ta.id != tb.id  # sanity
    finally:
        reset_session_tenant()
