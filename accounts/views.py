import os
import jwt
import requests
from django.conf import settings
from django.core.files.base import ContentFile
from rest_framework import status, viewsets
from rest_framework.generics import RetrieveAPIView, UpdateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import GoogleToken, User
from .serializers import UserSerializer


class GoogleLoginUrl(APIView):
    def get(self, request):
        request_url = requests.Request(
            "GET",
            "https://accounts.google.com/o/oauth2/v2/auth",
            params={
                "client_id": settings.GOOGLE_CLIENT_ID,
                "redirect_uri": f"{os.environ['CLIENT_HOST']}/api/auth/callback/google",
                "scope": "https://www.googleapis.com/auth/userinfo.email "
                "https://www.googleapis.com/auth/userinfo.profile",
                "access_type": "offline",
                "response_type": "code",
                "prompt": "consent",
            },
        )
        url = request_url.prepare().url
        return Response({"url": url})


def get_auth_tokens(code):
    response = requests.post(
        "https://oauth2.googleapis.com/token",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        params={
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": f"{os.environ['CLIENT_HOST']}/api/auth/callback/google",
            "grant_type": "authorization_code",
        },
        timeout=10,
    )
    return response.json()


class GoogleLogin(APIView):
    def post(self, request):
        code = request.data.get("code")
        token_data = get_auth_tokens(code)
        data = jwt.decode(token_data["id_token"], options={"verify_signature": False})
        email = data["email"]
        name = data["name"]
        avatar_url = data["picture"]
        google_access_token = token_data["access_token"]
        google_refresh_token = token_data["refresh_token"]
        user, created = User.objects.get_or_create(email=email, name=name)

        if created:
            if avatar_url:
                try:
                    response = requests.get(avatar_url, timeout=10)
                    if response.status_code == 200:
                        user.avatar.save(
                            f"{email}.png", ContentFile(response.content), save=True
                        )
                except:
                    pass

        google_token, _ = GoogleToken.objects.get_or_create(user=user)
        google_token.access_token = google_access_token
        google_token.refresh_token = google_refresh_token
        google_token.save()
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
        return Response(
            {
                "access": access_token,
                "refresh": refresh_token,
            },
            status=status.HTTP_200_OK,
        )


class UserUpdateView(UpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def perform_update(self, serializer):
        user_instance = serializer.instance
        if user_instance == self.request.user:
            serializer.save()
        return Response(
            {"error": "You are not authorized to update this user's data."},
            status=status.HTTP_403_FORBIDDEN,
        )


class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer

    def get_queryset(self):
        return User.objects.all()


class UserDetailsView(RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
