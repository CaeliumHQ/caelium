from django.urls import path

from api.views import create_media, verify_jwt_user


urlpatterns = [
    path("verify_jwt/", verify_jwt_user, name="verify_jwt_user"),
    path("create_media", create_media, name="api_create_media")
]
