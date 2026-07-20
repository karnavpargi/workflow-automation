"""DRF view for the admin-portal dashboard summary.

Returns a small JSON dict with three counts scoped to the caller's
tenant. The shape is locked by the ``Dashboard.tsx`` UI in the frontend
``Counts`` interface — keep them in sync.
"""

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from followups.models import Reminder
from invoices.models import Invoice
from onboarding.models import Client
from users.permissions import IsTenantMember


class DashboardSummaryView(APIView):
    """Aggregate counts for the admin dashboard.

    Returns ``{clients, open_invoices, due_followups}``. All counts are
    scoped to ``request.tenant``; cross-tenant data is not visible.
    """

    permission_classes = [IsAuthenticated, IsTenantMember]

    def get(self, request):
        """Return the three aggregate counts for the caller's tenant."""
        tenant = request.tenant
        return Response(
            {
                "clients": Client.objects.filter(tenant=tenant).count(),
                "open_invoices": Invoice.objects.filter(
                    tenant=tenant, status=Invoice.Status.ISSUED
                ).count(),
                "due_followups": Reminder.objects.filter(
                    tenant=tenant, status=Reminder.Status.PENDING
                ).count(),
            }
        )
