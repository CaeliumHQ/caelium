from django.urls import path

from .views import (ChatListView, ChatMessageListView, ChatParticipantAPIView, CreateChatAPIView,
                    CreateMessageAPIView)

urlpatterns = [
    path('', ChatListView.as_view(), name='user-chats'),
    path('get/<int:chat_id>/', ChatParticipantAPIView.as_view(), name='chat-participant-detail'),
    path('chats/<int:chat_id>/messages/', ChatMessageListView.as_view(), name='chat-messages'),
    path('messages/create/', CreateMessageAPIView.as_view(), name='create-message'),
    path('chats/create/', CreateChatAPIView.as_view(), name='create-chat'),
]
