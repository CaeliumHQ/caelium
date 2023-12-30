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
        fields = ('id', 'username', 'name', 'avatar')

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        token['name'] = user.name
        token['email'] = user.email
        token['avatar'] = os.environ['absolute_url']+'/'+str(user.avatar)
        token['birthdate'] = str(user.birthdate)
        return token


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('username', 'name', 'password', 'password2')

    def validate(self, attrs):
        if len(attrs['username']) <= 3:
            raise serializers.ValidationError(
              {"username": "username must be at least 3 characters"}
            )
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError(
                {"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        user = User.objects.create(
            username = validated_data['username'],
            name = validated_data['name'],
        )
        user.set_password(validated_data['password'])
        user.save()
        return user
