from rest_framework.serializers import ModelSerializer

from accounts.models import FCMToken, User


class UserSerializer(ModelSerializer):

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "name",
            "avatar",
            "location",
            "gender",
            "birthdate",
            "last_seen",
            "username",
        ]


class FCMTokenSerializer(ModelSerializer):
    class Meta:
        model = FCMToken
        fields = ["token"]
