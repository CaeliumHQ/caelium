from rest_framework import generics, viewsets
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import User
from .serializers import (MyTokenObtainPairSerializer, RegisterSerializer,
                          UserSerializer)


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    def get_queryset(self):
        return User.objects.all()

# class UserViewSet(viewsets.ModelViewSet):
#     serializer_class = UserSerializer

#     def get_queryset(self):
#         queryset = User.objects.all()
#         # Exclude the current user from the queryset
#         if self.request.user.is_authenticated:
#             queryset = queryset.exclude(pk=self.request.user.pk)
#         return queryset

class UserDetailsView(RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
