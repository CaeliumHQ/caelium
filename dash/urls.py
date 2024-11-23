from django.urls import path

from .views import LoginView, Stats

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("stats/", Stats.as_view(), name="stats"),
]
