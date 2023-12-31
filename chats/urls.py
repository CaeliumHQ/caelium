from django.urls import path

from . import views

urlpatterns = [
    path('', views.ChatViewSet.as_view({'get': 'list'})),
    path('messages/create/', views.MessageCreateView.as_view()),
]
