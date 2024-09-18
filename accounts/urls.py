from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

urlpatterns = [
    path("google/login/", views.GoogleLogin.as_view(), name="google_login"),
    path("google/auth_url/", views.GoogleLoginUrl.as_view(), name="google_auth_url"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("accounts/", views.UserViewSet.as_view({"get": "list"}), name="all_users"),
    path("accounts/<int:pk>/", views.UserDetailsView.as_view(), name="user_details"),
    path("update/<int:pk>/", views.UserUpdateView.as_view(), name="user_update"),
    path("update/fcm-token/", views.FCMTokenUpdateView.as_view(), name="update_fcm_token"),
]
