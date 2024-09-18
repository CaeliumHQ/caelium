import os

import jwt
import requests
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import IntegrityError
from rest_framework import status, viewsets
from rest_framework.generics import RetrieveAPIView, RetrieveUpdateAPIView, UpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from chats.models import Chat, Message

from .models import FCMToken, GoogleToken, User
from .serializers import FCMTokenSerializer, UserSerializer


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
                "include_granted_scopes": "true",
            },
        )
        url = request_url.prepare().url
        return Response({"url": url})


def get_auth_tokens(code, redirect_uri):
    response = requests.post(
        "https://oauth2.googleapis.com/token",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        params={
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        },
        timeout=10,
    )
    return response.json()


def refresh_access(refresh_token):
    response = requests.post(
        "https://oauth2.googleapis.com/token",
        params={
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        },
        timeout=10,
    )
    return response.json()


class GoogleLogin(APIView):
    def post(self, request):
        code = request.data.get("code")
        token_data = get_auth_tokens(code, f"{os.environ['CLIENT_HOST']}/api/auth/callback/google")
        data = jwt.decode(token_data["id_token"], options={"verify_signature": False})
        email = data["email"]
        name = data["name"]
        google_access_token = token_data["access_token"]
        google_refresh_token = token_data["refresh_token"]
        try:
            user, created = User.objects.get_or_create(email=email)
            if created:
                user.name = name
                user.save()
                # Fetch the admin user
                admin_user = User.objects.get(email="jeritalumkal@gmail.com")
                chat = Chat.objects.create()
                chat.participants.add(admin_user, user)
                chat.save()
                # Create the personalized welcome message
                Message.objects.create(
                    chat=chat,
                    sender=admin_user,
                    type="txt",
                    content=f"Hi {name},\n\n"
                    f"Welcome to Caelium! 🌟 We're excited to have you join us. "
                    f"I'm Jerit Baiju, The Founder of Caelium, and I want to personally thank you for becoming part of our community. "
                    f"If you have any questions, ideas, or just want to connect, feel free to reach out. "
                    f"Together, we can achieve great things! 🚀\n\n"
                    f"Best regards,\n"
                    f"Jerit",
                )

                try:
                    response = requests.get(data["picture"], timeout=10)
                    if response.status_code == 200:
                        user.avatar.save(f"{email}.png", ContentFile(response.content), save=True)
                except:
                    pass

        except IntegrityError:
            user = User.objects.get(email=email)

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


class FCMTokenUpdateView(RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = FCMTokenSerializer

    def get_object(self):
        # Try to get the FCM token for the current user, or create a new one
        obj, _ = FCMToken.objects.get_or_create(user=self.request.user)
        return obj
