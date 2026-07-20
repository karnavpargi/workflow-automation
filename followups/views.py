"""DRF views for the followups app."""

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from followups import services
from followups.models import Reminder
from followups.serializers import ReminderSerializer
from users.permissions import IsTenantMember


class ReminderViewSet(ModelViewSet):
    """List, create, retrieve, update, delete reminders in current tenant.

    Includes a ``cancel`` action that flips the status to ``cancelled``
    without deleting the historical record, and an ``approve`` action
    that promotes a ``DRAFT`` reminder to ``PENDING`` for the send
    path.
    """

    serializer_class = ReminderSerializer
    permission_classes = [IsTenantMember]

    def get_queryset(self):
        return Reminder.objects.filter(tenant=self.request.tenant).select_related(
            "rule"
        )

    def perform_create(self, serializer) -> None:
        """Bind the new reminder to the request's tenant."""
        serializer.save(tenant=self.request.tenant)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """Cancel a PENDING or SENT reminder (no-op if already cancelled)."""
        reminder = self.get_object()
        if reminder.status != Reminder.Status.CANCELLED:
            reminder.status = Reminder.Status.CANCELLED
            reminder.save(update_fields=["status"])
        serializer = self.get_serializer(reminder)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        """Promote a DRAFT reminder to PENDING for the send path."""
        reminder = self.get_object()
        services.approve_draft(reminder)
        reminder.refresh_from_db()
        serializer = self.get_serializer(reminder)
        return Response(serializer.data, status=status.HTTP_200_OK)
