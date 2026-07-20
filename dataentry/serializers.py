"""Serializers for the dataentry API."""

from rest_framework import serializers

from dataentry.models import DataEntryRecord


class DataEntryRecordSerializer(serializers.ModelSerializer):
    """DataEntryRecord read/write serializer.

    ``tenant`` and ``status`` are set by the service / pipeline layer,
    never the request body.
    """

    class Meta:
        model = DataEntryRecord
        fields = [
            "id",
            "source",
            "status",
            "raw",
            "mapped",
            "target_type",
            "error",
            "created_at",
        ]
        read_only_fields = ["id", "status", "mapped", "error", "created_at"]
