# TASK 2 PLACEHOLDER — replaced in Task 7.
"""Placeholder TenantMiddleware; replaced in Task 7."""
from django.http import HttpResponseNotFound


class TenantMiddleware:
    """No-op placeholder; resolved in Task 7."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.headers.get("X-Tenant-Slug"):
            request.tenant = None
            return self.get_response(request)
        # If a tenant header is sent but no real resolver exists, 404.
        return HttpResponseNotFound("tenant resolver not implemented")
