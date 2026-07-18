"""URL routes for the onboarding app."""

from django.urls import path

from onboarding.views import ClientListCreateView, ClientOnboardingStatusView

urlpatterns = [
    path("clients/", ClientListCreateView.as_view(), name="client-list-create"),
    path(
        "clients/<int:pk>/onboarding/",
        ClientOnboardingStatusView.as_view(),
        name="client-onboarding",
    ),
]
