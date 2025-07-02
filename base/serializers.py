from django.contrib.auth import get_user_model
from rest_framework import serializers

from base.models import Comment, Like, Post, Task
from cloud.models import CloudFile

User = get_user_model()


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ["name", "completed", "id"]

    def create(self, validated_data):
        validated_data["owner"] = self.context["request"].user
        return super().create(validated_data)


class PostUserSerializer(serializers.ModelSerializer):
    """Lightweight user serializer for posts"""

    class Meta:
        model = User
        fields = ["id", "name", "username", "avatar"]


class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = ["id", "post", "user", "created_at"]
        read_only_fields = ["id", "created_at"]


class CommentSerializer(serializers.ModelSerializer):
    owner = PostUserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "post", "owner", "content", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def create(self, validated_data):
        validated_data["owner"] = self.context["request"].user
        return super().create(validated_data)
