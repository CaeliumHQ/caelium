import os

from rest_framework.serializers import ModelSerializer, SerializerMethodField

from .models import FCMToken, User


class UserSerializer(ModelSerializer):
    avatar_url = SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "email", "name", "avatar", "avatar_url", "location", "gender", "birthdate", "last_seen"]

    def get_avatar_url(self, obj):
        if obj.avatar:
            return f"{os.environ['DJANGO_HOST']}{obj.avatar.url}"
        return None


class FCMTokenSerializer(ModelSerializer):
    class Meta:
        model = FCMToken
        fields = ["token"]
