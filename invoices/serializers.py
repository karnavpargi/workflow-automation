"""Serializers for the invoicing API."""

from rest_framework import serializers

from invoices.models import Invoice, LineItem, RecurringSchedule


class LineItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = LineItem
        fields = ["id", "description", "quantity", "unit_price"]


class InvoiceSerializer(serializers.ModelSerializer):
    lines = LineItemSerializer(many=True, read_only=True)

    class Meta:
        model = Invoice
        fields = [
            "id",
            "number",
            "status",
            "due_date",
            "total",
            "vendor_id",
            "pdf_path",
            "client",
            "created_at",
            "lines",
        ]
        read_only_fields = [
            "id",
            "total",
            "vendor_id",
            "pdf_path",
            "created_at",
            "status",
        ]


class RecurringScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecurringSchedule
        fields = ["id", "client", "template_lines", "cadence", "next_run", "is_active"]
