"""Tests for TenantMiddleware."""

from collections.abc import Callable
from typing import Any

import pytest
from django.http import Http404, HttpRequest, HttpResponse
from django.test import RequestFactory

from tenants.middleware import TenantMiddleware


def _mk_factory_app() -> tuple[Callable[[HttpRequest], HttpResponse], dict[str, Any]]:
    called: dict[str, Any] = {}

    def app(request: HttpRequest) -> HttpResponse:
        called["tenant"] = getattr(request, "tenant", None)
        return HttpResponse()

    return app, called


@pytest.mark.django_db
def test_middleware_sets_tenant_from_header() -> None:
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
def test_middleware_returns_404_unknown_tenant() -> None:
    """Unknown slugs raise Http404."""
    from users.models import User

    u = User.objects.create_user(email="a@x.io", password="p", username="a")
    app, _ = _mk_factory_app()
    mw = TenantMiddleware(app)
    req = RequestFactory().get("/", HTTP_X_TENANT_SLUG="nope")
    req.user = u
    with pytest.raises(Http404):
        mw(req)
