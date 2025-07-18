from django.urls import path

from api.views import verify_jwt_user


urlpatterns = [
    path("verify_jwt/", verify_jwt_user, name="verify_jwt_user"),
]
