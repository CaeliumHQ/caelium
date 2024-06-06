from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

urlpatterns = [
    path("google/logink/", views.GoogleLoginView.as_view(), name="google-login-t"),
    path("google/login/", views.GoogleLogin.as_view(), name="google-login"),
    path("google/auth_url/", views.GoogleLoginUrl.as_view(), name="google_auth_url"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("accounts/", views.UserViewSet.as_view({"get": "list"}), name="all_users"),
    path("accounts/<int:pk>/", views.UserDetailsView.as_view(), name="user-details"),
    path("update/<int:pk>/", views.UserUpdateView.as_view(), name="user-update"),
]
