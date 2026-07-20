"""DRF views for the dataentry app.

Three write endpoints (form, CSV upload, webhook) plus a list endpoint
for the auth'd record browser. The webhook endpoint is unauthenticated
and identifies tenants by URL slug; integrity is enforced with HMAC.
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import NotFound, ParseError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ReadOnlyModelViewSet

from dataentry.adapters import csv_xlsx
from dataentry.adapters import form as form_adapter
from dataentry.adapters.webhook import InvalidSignature, ingest_webhook
from dataentry.models import DataEntryRecord
from dataentry.serializers import DataEntryRecordSerializer
from users.permissions import IsTenantMember


class DataEntryRecordViewSet(ReadOnlyModelViewSet):
    """List / retrieve staged records in the caller's tenant."""

    serializer_class = DataEntryRecordSerializer
    permission_classes = [IsTenantMember]

    def get_queryset(self):
        return DataEntryRecord.objects.filter(tenant=self.request.tenant)


class FormSubmitView(APIView):
    """POST a form payload; returns the created PENDING record."""

    permission_classes = [IsTenantMember]

    def post(self, request):
        fields = request.data.get("fields")
        if not isinstance(fields, dict):
            raise ParseError("'fields' must be a JSON object")
        rec = form_adapter.ingest_form(request.tenant, fields)
        return Response(
            DataEntryRecordSerializer(rec).data, status=status.HTTP_201_CREATED
        )


class CSVUploadView(APIView):
    """POST a CSV file; returns the count of records created."""

    permission_classes = [IsTenantMember]

    def post(self, request):
        upload = request.FILES.get("file")
        if upload is None:
            raise ParseError("multipart 'file' field is required")
        recs = csv_xlsx.ingest_csv(request.tenant, upload)
        return Response({"count": len(recs)}, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([AllowAny])
def webhook_receive(request, tenant_slug: str):
    """Public webhook receiver; HMAC verifies integrity.

    The tenant is identified by URL slug (vendors POST to a stable URL).
    Requests without a matching signature are rejected with 401.
    """
    from tenants.models import Tenant

    try:
        tenant = Tenant.objects.get(slug=tenant_slug)
    except Tenant.DoesNotExist as exc:
        raise NotFound("unknown tenant") from exc
    signature = request.META.get("HTTP_X_SIGNATURE", "")
    try:
        rec = ingest_webhook(tenant, request.body, signature=signature or None)
    except InvalidSignature:
        return Response(
            {"error": "invalid signature"}, status=status.HTTP_401_UNAUTHORIZED
        )
    return Response(DataEntryRecordSerializer(rec).data, status=status.HTTP_201_CREATED)
