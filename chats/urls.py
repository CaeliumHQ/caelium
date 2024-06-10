from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"", views.ChatViewSet, basename="chats")
router.register(r"messages/(?P<chat_id>\d+)", views.MessageViewSet, basename="messages")

urlpatterns = [
    path("users/", views.ChatUsers.as_view({"get": "list"}), name="chat_users")
]

urlpatterns += router.urls
