from django.urls import path

from . import views

urlpatterns = [
    path('', views.ChatViewSet.as_view({'get': 'list'})),
    path('start/', views.StartChatView.as_view(), name='start-chat'),
    path('messages/create/', views.MessageCreateView.as_view()),
]
