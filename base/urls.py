from rest_framework.routers import DefaultRouter

from .views import EventViewSet, TaskViewSet

router = DefaultRouter()

router.register(r"tasks", TaskViewSet, basename="tasks")
router.register(r"events", EventViewSet, basename="events")
urlpatterns = router.urls
