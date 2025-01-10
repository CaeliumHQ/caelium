from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"", views.ChatViewSet, basename="chats")
router.register(r"messages/(?P<chat_id>\d+)", views.MessageViewSet, basename="messages")

urlpatterns = [
    path("users/", views.ChatUsers.as_view({"get": "list"}), name="chat_users"),
    path("<int:chat_id>/start_call/", views.InitiateCallAPI.as_view(), name="start_call"),
    path("join_call/", views.JoinCallAPI.as_view(), name="join_call"),
]

urlpatterns += router.urls
