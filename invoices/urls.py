"""URL routes for the invoicing app."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from invoices.views import InvoiceViewSet, RecurringScheduleViewSet

router = DefaultRouter()
router.register("invoices", InvoiceViewSet, basename="invoice")
router.register(
    "recurring-schedules", RecurringScheduleViewSet, basename="recurring-schedule"
)

urlpatterns = [
    path("", include(router.urls)),
]
