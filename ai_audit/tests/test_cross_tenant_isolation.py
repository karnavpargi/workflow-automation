"""Cross-tenant isolation contract for ai_audit."""

from collections.abc import Generator

import pytest
from django.db import connection

from tenants.rls import enable_rls_on, reset_session_tenant, set_session_tenant

_RLS_TABLES = ("ai_audit_llmcall",)


@pytest.fixture(autouse=True)
def _restore_rls_state() -> Generator[None, None, None]:
    """Make sure RLS is off for the ai_audit tables around this test."""
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
def test_rls_blocks_cross_tenant_llm_calls():
    """Setting a session tenant filters LlmCall rows to that tenant."""
    from ai_audit.services import record_llm_call
    from tenants import services as tsvc
    from users.models import User

    ua = User.objects.create_user(email="a@x.io", password="p", username="a")
    ub = User.objects.create_user(email="b@x.io", password="p", username="b")
    ta = tsvc.create_tenant(name="A", slug="a", admin=ua)
    tb = tsvc.create_tenant(name="B", slug="b", admin=ub)
    record_llm_call(
        tenant=ta,
        agent_name="x",
        input_hash="a" * 64,
        output_hash="b" * 64,
    )
    record_llm_call(
        tenant=tb,
        agent_name="x",
        input_hash="c" * 64,
        output_hash="d" * 64,
    )

    enable_rls_on("ai_audit_llmcall")
    try:
        set_session_tenant(ta.id)
        with connection.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM ai_audit_llmcall")
            (count,) = cur.fetchone()
        assert count == 1
    finally:
        reset_session_tenant()
