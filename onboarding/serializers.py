"""Serializers for the onboarding API."""

from rest_framework import serializers

from onboarding.models import Client, OnboardingRun, OnboardingStep


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ["id", "name", "email", "created_at"]
        read_only_fields = ["id", "created_at"]


class OnboardingStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = OnboardingStep
        fields = ["id", "kind", "order", "config", "delay_seconds"]


class OnboardingRunSerializer(serializers.ModelSerializer):
    steps = OnboardingStepSerializer(many=True, read_only=True)
    template_name = serializers.CharField(source="template.name", read_only=True)

    class Meta:
        model = OnboardingRun
        fields = [
            "id",
            "client",
            "template",
            "template_name",
            "status",
            "created_at",
            "steps",
        ]
        read_only_fields = fields


class OnboardingStatusSerializer(serializers.Serializer):
    """Response shape for GET /api/clients/{id}/onboarding/."""

    client = ClientSerializer()
    runs = OnboardingRunSerializer(many=True)
