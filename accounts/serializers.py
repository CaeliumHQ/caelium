from rest_framework.serializers import ModelSerializer
from .models import FCMToken, User


class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'avatar', 'location', 'gender', 'birthdate', 'last_seen']


class FCMTokenSerializer(ModelSerializer):
    class Meta:
        model = FCMToken
        fields = ["token"]
