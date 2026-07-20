"""Tests proving RLS blocks cross-tenant reads when tenant_id is set."""

from collections.abc import Generator

import pytest
from django.db import connection


@pytest.fixture(autouse=True)
def _restore_rls_state() -> Generator[None, None, None]:
    """Make sure RLS is off going into the test, off coming out.

    The session-scoped ``django_db_setup`` disables RLS so the 14
    non-RLS tests can create tenant rows without setting the GUC.
    The RLS test in this module manually re-enables RLS between its
    data setup and its assertion; this fixture guarantees the next
    test in the session starts with RLS disabled again.
    """
    with connection.cursor() as cur:
        cur.execute("ALTER TABLE tenants_tenant DISABLE ROW LEVEL SECURITY")
        cur.execute("DROP POLICY IF EXISTS tenant_isolation ON tenants_tenant")
    yield
    with connection.cursor() as cur:
        cur.execute("ALTER TABLE tenants_tenant DISABLE ROW LEVEL SECURITY")
        cur.execute("DROP POLICY IF EXISTS tenant_isolation ON tenants_tenant")


@pytest.mark.django_db
def test_rls_blocks_cross_tenant_select() -> None:
    """With SET app.tenant_id and policies enabled, only own rows return."""
    # Step 1: insert with RLS off (session fixture ensures this).
    with connection.cursor() as cur:
        cur.execute(
            "INSERT INTO tenants_tenant "
            "(name, slug, created_at, is_active, webhook_secret) "
            "VALUES ('A','a',now(),true,''),('B','b',now(),true,'') "
            "RETURNING id"
        )
        inserted_ids = [r[0] for r in cur.fetchall()]
    # Step 2: re-enable RLS so the policy actually applies.
    from tenants.rls import enable_rls_on

    enable_rls_on("tenants_tenant")
    # Step 3: set the GUC to the just-inserted row's id (sequences
    # don't roll back between tests, so the id isn't always 1) and
    # verify only own rows are visible.
    own_id = inserted_ids[0]
    with connection.cursor() as cur:
        cur.execute("SET app.tenant_id = %s", [own_id])
        cur.execute("SELECT slug FROM tenants_tenant")
        rows = [r[0] for r in cur.fetchall()]
    assert rows == ["a"]
