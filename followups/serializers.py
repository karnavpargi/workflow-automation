"""Serializers for the followups API."""

from rest_framework import serializers

from followups.models import FollowupRule, Reminder


class FollowupRuleSerializer(serializers.ModelSerializer):
    """FollowupRule read/write serializer."""

    class Meta:
        model = FollowupRule
        fields = [
            "id",
            "name",
            "channel",
            "offset_days",
            "template",
        ]
        read_only_fields = ["id"]


class ReminderSerializer(serializers.ModelSerializer):
    """Reminder read/write serializer.

    ``tenant`` and ``status`` are set by the service layer (or by
    dedicated actions), never by the request body.
    """

    class Meta:
        model = Reminder
        fields = [
            "id",
            "rule",
            "subject",
            "due_at",
            "recipient_email",
            "status",
            "context",
            "created_at",
        ]
        read_only_fields = ["id", "status", "created_at"]
