"""DRF views for the invoicing app."""

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from invoices import services
from invoices.models import Invoice, RecurringSchedule
from invoices.serializers import InvoiceSerializer, RecurringScheduleSerializer
from users.permissions import IsTenantMember


class InvoiceViewSet(ModelViewSet):
    """List, create, retrieve, update, delete invoices in the current tenant."""

    serializer_class = InvoiceSerializer
    permission_classes = [IsTenantMember]

    def get_queryset(self):
        return Invoice.objects.filter(tenant=self.request.tenant).prefetch_related(
            "lines"
        )

    @action(detail=True, methods=["post"])
    def issue(self, request, pk=None):
        """Issue the invoice (Flow B)."""
        invoice = self.get_object()
        services.issue_invoice(invoice=invoice)
        serializer = self.get_serializer(invoice)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"])
    def pdf_url(self, request, pk=None):
        """Return a presigned URL to the invoice PDF."""
        invoice = self.get_object()
        if not invoice.pdf_path:
            return Response(
                {"error": "Invoice has no PDF"}, status=status.HTTP_404_NOT_FOUND
            )
        from integrations.models import IntegrationConfig
        from integrations.services import get_adapter

        try:
            storage = get_adapter(
                invoice.tenant, IntegrationConfig.Kind.STORAGE, vendor="minio"
            )
            url = storage.get_url(invoice.pdf_path)
        except Exception as exc:  # noqa: BLE001
            return Response(
                {"error": f"Storage error: {exc}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Response({"url": url})


class RecurringScheduleViewSet(ModelViewSet):
    """List, create, retrieve, update, delete recurring schedules."""

    serializer_class = RecurringScheduleSerializer
    permission_classes = [IsTenantMember]

    def get_queryset(self):
        return RecurringSchedule.objects.filter(tenant=self.request.tenant)
