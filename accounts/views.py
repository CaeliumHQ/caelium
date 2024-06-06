import requests
from django.conf import settings
from google.oauth2 import id_token
from rest_framework import status, viewsets
from rest_framework.generics import RetrieveAPIView, UpdateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import GoogleToken, User
from .serializers import UserSerializer


class GoogleLoginView(APIView):
    def post(self, request):
        token = request.data.get("token")
        try:
            id_info = id_token.verify_oauth2_token(
                token,
                requests.Request(),
                settings.GOOGLE_CLIENT_ID,
            )
            if "email" not in id_info or "name" not in id_info:
                return Response(
                    {"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST
                )

            email = id_info["email"]
            name = id_info["name"]
            access_token = request.data["google_access_token"]
            refresh_token = request.data["google_refresh_token"]
            user, _ = User.objects.get_or_create(email=email, name=name)
            google_token, _ = GoogleToken.objects.get_or_create(user=user)
            google_token.access_token = access_token
            google_token.refresh_token = refresh_token
            google_token.save()

            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)
            serializer = UserSerializer(user)
            return Response(
                {
                    "user": serializer.data,
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                },
                status=status.HTTP_200_OK,
            )

        except ValueError:
            return Response(
                {"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST
            )


class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer

    def get_queryset(self):
        return User.objects.all()


class UserDetailsView(RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


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
