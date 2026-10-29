from rest_framework.routers import SimpleRouter

from apps.timetracking.views import TimeEntryViewSet

router = SimpleRouter()
router.register("time-entries", TimeEntryViewSet, basename="time-entry")

urlpatterns = router.urls
