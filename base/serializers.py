import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
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


class PostSerializer(serializers.ModelSerializer):
    user = PostUserSerializer(source="owner", read_only=True)
    likes = serializers.SerializerMethodField()
    comments = serializers.SerializerMethodField()
    time = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    file = serializers.ImageField(write_only=True, required=False)
    caption = serializers.CharField(max_length=200, required=False, allow_blank=True)
    tagged_users = serializers.ListField(child=serializers.CharField(), write_only=True, required=False)
    allow_comments = serializers.BooleanField(default=True)
    content_url = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            "id",
            "user",
            "content",
            "content_url",
            "caption",
            "likes",
            "comments",
            "time",
            "is_liked",
            "created_at",
            "file",
            "tagged_users",
            "allow_comments",
        ]
        read_only_fields = ["id", "created_at", "content"]

    def get_content_url(self, obj):
        """Return the URL for the content file"""
        if obj.content and obj.content.local_path:
            return f"/media/{obj.content.local_path}"
        return None

    def get_likes(self, obj):
        return obj.likes_count()

    def get_comments(self, obj):
        return obj.comments.count()

    def get_time(self, obj):
        """Return time in a format similar to your frontend expectation"""
        now = timezone.now()
        diff = now - obj.created_at

        if diff.days > 0:
            return f"{diff.days}d"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours}h"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes}m"
        else:
            return "now"

    def get_is_liked(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False

    def create(self, validated_data):
        # Extract file and other data
        uploaded_file = validated_data.pop("file", None)
        tagged_user_ids = validated_data.pop("tagged_users", [])

        if not uploaded_file:
            raise serializers.ValidationError("File is required for creating a post")

        # Validate file size (10MB limit)
        max_size = 10 * 1024 * 1024  # 10MB in bytes
        if uploaded_file.size > max_size:
            raise serializers.ValidationError("File size cannot exceed 10MB")

        # Create the post first
        validated_data["owner"] = self.context["request"].user
        post = super().create(validated_data)

        # Create directory for this post
        post_dir = f"posts/{post.id}"
        full_post_dir = os.path.join(settings.MEDIA_ROOT, post_dir)
        os.makedirs(full_post_dir, exist_ok=True)

        # Save the file
        filename = f"{uploaded_file.name}"
        file_path = os.path.join(post_dir, filename)
        full_file_path = os.path.join(settings.MEDIA_ROOT, file_path)

        # Write the file to disk
        with open(full_file_path, "wb+") as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)

        # Create File model instance
        file_instance = CloudFile.objects.create(
            name=uploaded_file.name,
            owner=post.owner,
            parent=None,  # No parent for post files
            size=uploaded_file.size,
            mime_type=uploaded_file.content_type,
            created_at=timezone.now(),
            local_path=file_path,
            tier="hot",  # Set tier as hot
            category="post",  # Set category as post
            upload_status="completed",
        )

        # Update the post with the file content
        post.content = file_instance
        post.save()

        # Handle tagged users
        if tagged_user_ids:
            try:
                tagged_users = User.objects.filter(id__in=tagged_user_ids)
                post.tagged_users.set(tagged_users)
            except (ValueError, User.DoesNotExist):
                pass  # Ignore invalid user IDs

        return post


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
