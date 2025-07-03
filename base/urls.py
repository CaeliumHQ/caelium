from rest_framework.routers import DefaultRouter

from base.views import CommentViewSet, LikeViewSet, TaskViewSet

router = DefaultRouter()

router.register(r"tasks", TaskViewSet, basename="tasks")
router.register(r"likes", LikeViewSet, basename="likes")
router.register(r"comments", CommentViewSet, basename="comments")

urlpatterns = router.urls
