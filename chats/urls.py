from django.urls import path

from . import views

urlpatterns = [
    path('', views.ChatViewSet.as_view({'get': 'list'})),
    path('messages/<pk>/', views.MessagesView.as_view()),
    path('create/', views.ChatCreateView.as_view()),
    path('messages/create/', views.MessageCreateView.as_view()),
]
