"""URL routes for the followups app."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from followups.views import ReminderViewSet

router = DefaultRouter()
router.register("reminders", ReminderViewSet, basename="reminder")

urlpatterns = [
    path("", include(router.urls)),
]
