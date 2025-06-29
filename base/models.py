from django.db import models

from accounts.models import User
from cloud.models import MediaFile


class Post(models.Model):
    media = models.ManyToManyField(MediaFile, related_name="posts")
    caption = models.TextField(max_length=200, blank=True, null=True, help_text="Caption for the post")
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    tagged_users = models.ManyToManyField(
        User, related_name="tagged_posts", blank=True, help_text="Users tagged in this post"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    allow_comments = models.BooleanField(default=True, help_text="Whether comments are allowed on this post")

    def likes_count(self):
        """Return the number of likes for this post"""
        return self.likes.count()

    def __str__(self):
        return f"Post by {self.owner.username} at {self.created_at}"


class Like(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("post", "user")  # Prevent duplicate likes

    def __str__(self):
        return f"{self.user.username} liked {self.post.id}"


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.owner.username} - {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"


class Task(models.Model):
    name = models.CharField(max_length=255)
    completed = models.BooleanField(default=False)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    space = models.CharField(
        max_length=255,
        choices=(
            ("personal", "Personal"),
            ("partner", "Partner"),
            ("family", "Family"),
        ),
    )

    def __str__(self):
        return f"{self.owner} - {self.name}"
