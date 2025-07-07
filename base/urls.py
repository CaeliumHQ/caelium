from rest_framework.routers import DefaultRouter

from base.views import CommentViewSet, LikeViewSet, TaskViewSet, PostViewSet

router = DefaultRouter()

router.register(r"tasks", TaskViewSet, basename="tasks")
router.register(r"likes", LikeViewSet, basename="likes")
router.register(r"comments", CommentViewSet, basename="comments")
router.register(r"posts", PostViewSet, basename="posts")

urlpatterns = router.urls
