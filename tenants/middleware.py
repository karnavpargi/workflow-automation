"""Middleware that resolves the current tenant from the request.

Resolution order:
1. ``X-Tenant-Slug`` header (for API clients).
2. Subdomain prefix (future).

On unknown slug returns 404. The resolved tenant is attached to
``request.tenant`` for downstream views and querysets.
"""

from django.http import Http404

from tenants.models import Tenant


class TenantMiddleware:
    """DRF-friendly middleware to set ``request.tenant``.

    Attributes:
        get_response: The next handler in the chain.
    """

    def __init__(self, get_response):
        """Store the next response handler.

        Args:
            get_response: Standard Django middleware callable.
        """
        self.get_response = get_response

    def __call__(self, request):
        """Resolve and attach the tenant, then delegate downstream.

        Args:
            request: The incoming HttpRequest.

        Returns:
            The downstream response, or 404 if tenant is missing.
        """
        slug = request.headers.get("X-Tenant-Slug")
        if not slug:
            request.tenant = None
            return self.get_response(request)
        try:
            request.tenant = Tenant.objects.get(slug=slug, is_active=True)
        except Tenant.DoesNotExist as exc:
            raise Http404("unknown tenant") from exc
        return self.get_response(request)
