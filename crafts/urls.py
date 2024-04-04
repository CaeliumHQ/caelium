from rest_framework.routers import DefaultRouter

from .views import CraftViewSet

router = DefaultRouter()

router.register(r"", CraftViewSet, basename="crafts")
urlpatterns = router.urls
