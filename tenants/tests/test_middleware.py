"""Tests for TenantMiddleware."""

import pytest
from django.test import RequestFactory

from tenants.middleware import TenantMiddleware


def _mk_factory_app():
    called = {}

    def app(request):
        called["tenant"] = getattr(request, "tenant", None)
        return None

    return app, called


@pytest.mark.django_db
def test_middleware_sets_tenant_from_header():
    """Middleware resolves tenant from X-Tenant-Slug header."""
    from tenants import services
    from users.models import User

    u = User.objects.create_user(email="a@x.io", password="p", username="a")
    services.create_tenant(name="Acme", slug="acme", admin=u)
    app, called = _mk_factory_app()
    mw = TenantMiddleware(app)
    req = RequestFactory().get("/", HTTP_X_TENANT_SLUG="acme")
    req.user = u
    mw(req)
    assert called["tenant"].slug == "acme"


@pytest.mark.django_db
def test_middleware_returns_404_unknown_tenant():
    """Unknown slugs produce 404."""
    from users.models import User

    u = User.objects.create_user(email="a@x.io", password="p", username="a")
    app, _ = _mk_factory_app()
    mw = TenantMiddleware(app)
    req = RequestFactory().get("/", HTTP_X_TENANT_SLUG="nope")
    req.user = u
    resp = mw(req)
    assert resp.status_code == 404
