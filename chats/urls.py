from django.urls import path

from .views import (ChatMessageListView, CreateChatAPIView,
                    CreateMessageAPIView, UserChatListView)

urlpatterns = [
    path('', UserChatListView.as_view(), name='user-chats'),
    path('chats/<int:chat_id>/messages/', ChatMessageListView.as_view(), name='chat-messages'),
    path('messages/create/', CreateMessageAPIView.as_view(), name='create-message'),
    path('chats/create/', CreateChatAPIView.as_view(), name='create-chat'),
]
