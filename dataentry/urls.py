"""URL routes for the dataentry app."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from dataentry.views import (
    CSVUploadView,
    DataEntryRecordViewSet,
    FormSubmitView,
    webhook_receive,
)

router = DefaultRouter()
router.register("records", DataEntryRecordViewSet, basename="dataentry-record")

urlpatterns = [
    path("", include(router.urls)),
    path("form/", FormSubmitView.as_view(), name="dataentry-form"),
    path("csv/", CSVUploadView.as_view(), name="dataentry-csv"),
    path("webhook/<slug:tenant_slug>/", webhook_receive, name="dataentry-webhook"),
]
