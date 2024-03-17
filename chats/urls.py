from django.urls import path

from . import views

urlpatterns = [
    path('create/', views.CreateChat.as_view(), name='create_chat'),
    # path('list_chats/', views.list_chats, name='list_chats'),
    # path('create_message/<int:chat_id>/', views.create_message, name='create_message'),
    # path('list_messages/<int:chat_id>/', views.list_messages, name='list_messages'),
]
