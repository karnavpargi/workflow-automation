"""DRF views for the onboarding app."""

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from onboarding.models import Client, OnboardingRun
from onboarding.serializers import (
    ClientSerializer,
    OnboardingStatusSerializer,
)
from users.permissions import IsTenantMember


class ClientListCreateView(generics.ListCreateAPIView):
    """List and create clients in the current tenant."""

    serializer_class = ClientSerializer
    permission_classes = [IsTenantMember]

    def get_queryset(self):
        return Client.objects.filter(tenant=self.request.tenant)

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.tenant)


class ClientOnboardingStatusView(APIView):
    """Get the onboarding status for a client."""

    permission_classes = [IsTenantMember]

    def get(self, request, pk):
        client = Client.objects.filter(tenant=request.tenant, pk=pk).first()
        if client is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        runs = OnboardingRun.objects.filter(client=client).prefetch_related(
            "template__steps"
        )
        return Response(
            OnboardingStatusSerializer({"client": client, "runs": runs}).data
        )
