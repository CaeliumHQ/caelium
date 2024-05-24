from rest_framework.routers import DefaultRouter

from .views import MediaFileViewSet

router = DefaultRouter()
router.register(r"", MediaFileViewSet, basename='media_files')
urlpatterns = router.urls
