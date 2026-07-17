"""Cross-tenant isolation contract; every future tenant-scoped model must
pass this same shape. This first test pins the audit table, which is
already tenant-scoped, as the reference."""

import pytest
from django.db import connection

from tenants.rls import reset_session_tenant, set_session_tenant


@pytest.mark.django_db
def test_rls_blocks_cross_tenant_audit_rows():
    """Setting a session tenant and querying audit rows only returns own."""
    from audit import services
    from tenants import services as tsvc
    from users.models import User

    ua = User.objects.create_user(email="a@x.io", password="p", username="a")
    ub = User.objects.create_user(email="b@x.io", password="p", username="b")
    ta = tsvc.create_tenant(name="A", slug="a", admin=ua)
    tb = tsvc.create_tenant(name="B", slug="b", admin=ub)
    services.log(tenant=ta, actor=ua, event="x")
    services.log(tenant=tb, actor=ub, event="x")
    try:
        set_session_tenant(ta.id)
        with connection.cursor() as cur:
            cur.execute("SELECT tenant_id FROM audit_auditlog")
            rows = [r[0] for r in cur.fetchall()]
        assert rows == [ta.id]
    finally:
        reset_session_tenant()
