"""Tests proving RLS blocks cross-tenant reads when tenant_id is set."""

import pytest
from django.db import connection


@pytest.mark.django_db
def test_rls_blocks_cross_tenant_select() -> None:
    """With SET LOCAL app.tenant_id and policies enabled, only own rows return."""
    with connection.cursor() as cur:
        cur.execute(
            "INSERT INTO tenants_tenant (name, slug, created_at, is_active) "
            "VALUES ('A','a',now(),true),('B','b',now(),true)"
        )
        cur.execute("SET LOCAL app.tenant_id = %s", [1])
        cur.execute("SELECT slug FROM tenants_tenant")
        rows = [r[0] for r in cur.fetchall()]
    assert rows == ["a"]
