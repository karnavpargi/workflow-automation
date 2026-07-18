"""Cross-tenant isolation contract for TaskRecord (and Event)."""

from collections.abc import Generator

import pytest
from django.db import connection

from tenants.rls import enable_rls_on, reset_session_tenant, set_session_tenant


@pytest.fixture(autouse=True)
def _restore_workflows_rls_state() -> Generator[None, None, None]:
    """Make sure RLS is off for the workflows tables around this test.

    The session-scoped ``django_db_setup`` disables RLS on every
    tenant-scoped table so the non-RLS tests can create tenant rows
    without setting the GUC. This test re-enables RLS on the workflows
    tables between data setup and assertion; this fixture guarantees the
    next test in the session starts with RLS disabled again.
    """
    with connection.cursor() as cur:
        for table in ("workflows_event", "workflows_taskrecord"):
            cur.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
            cur.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")
    yield
    with connection.cursor() as cur:
        for table in ("workflows_event", "workflows_taskrecord"):
            cur.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
            cur.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")


@pytest.mark.django_db(transaction=True)
def test_rls_blocks_cross_tenant_task_records() -> None:
    """Setting a session tenant filters TaskRecord rows to that tenant.

    Marked ``transaction=True`` because :func:`enable_rls_on` issues
    DDL (``ALTER TABLE``) and PostgreSQL refuses to run DDL while the
    current transaction holds pending trigger events from the
    append-only ``audit_auditlog`` triggers (which fire as part of
    tenant creation). The transaction marker drops the per-test
    savepoint so each statement (including the DDL) is its own
    micro-transaction.
    """
    from tenants import services as tsvc
    from users.models import User
    from workflows import registry, services

    def handler(event):  # noqa: ANN001
        return None

    registry.register("x", handler)

    # Step 1: set up data with RLS off (autouse fixture ensures this).
    ua = User.objects.create_user(email="a@x.io", password="p", username="a")
    ub = User.objects.create_user(email="b@x.io", password="p", username="b")
    ta = tsvc.create_tenant(name="A", slug="a", admin=ua)
    tb = tsvc.create_tenant(name="B", slug="b", admin=ub)
    services.emit_event(
        tenant=ta, name="x", payload={}, task_name="t", entity_id="1", step="s"
    )
    services.emit_event(
        tenant=tb, name="x", payload={}, task_name="t", entity_id="1", step="s"
    )
    # Step 2: re-enable RLS so the policy actually applies to the SELECT.
    enable_rls_on("workflows_taskrecord")
    # Step 3: set the GUC and verify only own rows are visible.
    try:
        set_session_tenant(ta.id)
        with connection.cursor() as cur:
            cur.execute("SELECT tenant_id FROM workflows_taskrecord")
            rows = [r[0] for r in cur.fetchall()]
        assert rows, "expected at least one TaskRecord row for tenant A"
        assert all(r == ta.id for r in rows), rows
        assert ta.id != tb.id  # sanity
    finally:
        reset_session_tenant()
