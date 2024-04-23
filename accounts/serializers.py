import os

from django.contrib.auth.password_validation import validate_password
from dotenv import load_dotenv
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import User

load_dotenv()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "name",
            "avatar",
            "email",
            "birthdate",
            "location",
            "gender",
        )


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "username",
            "name",
            "avatar",
            "email",
            "birthdate",
            "location",
            "gender",
        )


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["id"] = user.id
        token["username"] = user.username
        token["name"] = user.name
        token["email"] = user.email
        token["avatar"] = os.environ["absolute_url"] + "/" + str(user.avatar)
        token["birthdate"] = str(user.birthdate)
        return token


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )

    class Meta:
        model = User
        fields = ("username", "name", "password")

    def validate(self, attrs):
        if len(attrs["username"]) <= 3:
            raise serializers.ValidationError(
                {"username": "username must be at least 3 characters"}
            )
        return attrs

    def create(self, validated_data):
        user = User.objects.create(
            username=str(validated_data["username"]).casefold(),
            name=validated_data["name"],
        )
        user.set_password(validated_data["password"])
        user.save()
        return user
