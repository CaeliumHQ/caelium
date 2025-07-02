from django.urls import path

from dash.views import LoginView, Stats, UserDetailView, UserListView

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("stats/", Stats.as_view(), name="stats"),
    path("users/", UserListView.as_view(), name="user-list"),
    path("users/<int:pk>/", UserDetailView.as_view(), name="user-detail"),
]
