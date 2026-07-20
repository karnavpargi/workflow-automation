"""Cross-tenant isolation contract for followups."""

from collections.abc import Generator

import pytest
from django.db import connection

from tenants.rls import enable_rls_on, reset_session_tenant, set_session_tenant

_RLS_TABLES = (
    "followups_followuprule",
    "followups_reminder",
)


@pytest.fixture(autouse=True)
def _restore_rls_state() -> Generator[None, None, None]:
    """Make sure RLS is off for the followups tables around this test.

    The session-scoped ``django_db_setup`` disables RLS for every table
    in :data:`tenants.rls.TENANT_SCOPED_TABLES` so the rest of the test
    suite can create tenant rows without setting the GUC. This test
    manually re-enables RLS on the followups tables between its data
    setup and its assertion; this fixture guarantees the next test in
    the session starts with RLS disabled again.
    """
    with connection.cursor() as cur:
        for table in _RLS_TABLES:
            cur.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
            cur.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")
    yield
    with connection.cursor() as cur:
        for table in _RLS_TABLES:
            cur.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
            cur.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")


@pytest.mark.django_db(transaction=True)
def test_rls_blocks_cross_tenant_reminders():
    """Setting a session tenant filters Reminder rows to that tenant."""
    from django.utils import timezone

    from followups.models import Reminder
    from tenants import services as tsvc
    from users.models import User

    ua = User.objects.create_user(email="a@x.io", password="p", username="a")
    ub = User.objects.create_user(email="b@x.io", password="p", username="b")
    ta = tsvc.create_tenant(name="A", slug="a", admin=ua)
    tb = tsvc.create_tenant(name="B", slug="b", admin=ub)
    now = timezone.now()
    Reminder.objects.create(tenant=ta, subject="A-1", due_at=now)
    Reminder.objects.create(tenant=tb, subject="B-1", due_at=now)

    # Re-enable RLS so the policy actually applies to the SELECT.
    enable_rls_on("followups_reminder")
    try:
        set_session_tenant(ta.id)
        with connection.cursor() as cur:
            cur.execute("SELECT subject FROM followups_reminder")
            rows = [r[0] for r in cur.fetchall()]
        assert rows, "expected at least one reminder row for tenant A"
        assert all(r == "A-1" for r in rows), rows
    finally:
        reset_session_tenant()
