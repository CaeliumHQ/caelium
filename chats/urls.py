from rest_framework.routers import DefaultRouter

from .views import ChatViewSet, MessageViewSet

router = DefaultRouter()
router.register(r"", ChatViewSet, basename="chats")
router.register(r"messages/(?P<chat_id>\d+)", MessageViewSet, basename="messages")
# router.register(r'messages/', MessageViewSet)
urlpatterns = router.urls
