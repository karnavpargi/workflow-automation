"""URL routes for the dashboard app."""

from django.urls import path

from dashboard.views import DashboardSummaryView

urlpatterns = [
    path("", DashboardSummaryView.as_view(), name="dashboard-summary"),
]
