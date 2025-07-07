from django.contrib.auth import get_user_model
from rest_framework import serializers

from base.models import Comment, Like, Post, Task
from cloud.models import MediaFile

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


class PostSerializer(serializers.ModelSerializer):
    owner = PostUserSerializer(read_only=True)

    class Meta:
        model = Post
        fields = '__all__'
        read_only_fields = ["id", "created_at", "updated_at"]


class PostCreateSerializer(serializers.ModelSerializer):
    file = serializers.ImageField()

    class Meta:
        model = Post
        exclude = ["owner", "created_at", "updated_at", "media"]

    def create(self, validated_data):
        # Extract the custom files field
        files = validated_data.pop("files", [])

        # Set the owner
        validated_data["owner"] = self.context["request"].user

        # Create the post instance
        post = super().create(validated_data)

        # Handle the uploaded files (example processing)
        for _ in files:
            # MediaFile.objects.create()
            # Process each file - save to media storage, create Media objects, etc.
            # Example: create media objects and associate with the post
            pass

        return post

    def validate_files(self, files):
        """Custom validation for files"""
        if len(files) > 10:  # Limit to 10 files
            raise serializers.ValidationError("Maximum 10 files allowed")

        for file in files:
            # Validate file size (e.g., max 10MB)
            if file.size > 10 * 1024 * 1024:
                raise serializers.ValidationError(f"File {file.name} is too large. Maximum size is 10MB")

            # Validate file type
            allowed_types = ["image/jpeg", "image/png", "image/gif", "video/mp4"]
            if file.content_type not in allowed_types:
                raise serializers.ValidationError(f"File type {file.content_type} not allowed")

        return files


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
