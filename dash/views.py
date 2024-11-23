from django.contrib.auth import authenticate
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import User
from chats.models import Chat, Message
from crafts.models import Craft


class LoginView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request, *args, **kwargs):
        email = request.data.get("email")
        password = request.data.get("password")
        user = authenticate(username=email, password=password)
        if user is not None and user.is_superuser is True:
            refresh = RefreshToken.for_user(user)
            return Response(
                {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                }
            )
        return Response({"error": "Invalid Credentials"}, status=status.HTTP_401_UNAUTHORIZED)


class Stats(APIView):
    permission_classes = (permissions.IsAdminUser,)
    def get(self, request, *args, **kwargs):
        stats = {
            "users": User.objects.count(),
            "messages": Message.objects.count(),
            "chats": Chat.objects.count(),
            "crafts": Craft.objects.count(),
        }
        return Response(stats)
