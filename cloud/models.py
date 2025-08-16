import uuid

from django.db import models

from accounts.models import User


class MediaFile(models.Model):
    appwrite_id = models.CharField(max_length=255, unique=True, help_text="Unique identifier for the media file in Appwrite")
    g_drive_id = models.CharField(max_length=255, unique=True, help_text="Google Drive ID if applicable")
    filename = models.CharField(max_length=255)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    encryption_key = models.TextField(blank=True, null=True)
    encryption_iv = models.TextField(blank=True, null=True)
    mime_type = models.CharField(max_length=100)
    size = models.BigIntegerField()
    file_type = models.CharField(
        max_length=20,
        choices=[("image", "Image"), ("video", "Video"), ("audio", "Audio"), ("document", "Document"), ("other", "Other")],
    )
    storage_tier = models.CharField(max_length=20, choices=[("hot", "Hot"), ("cold", "Cold")], default="hot")
    timestamp = models.DateTimeField()
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.file_type.upper()} ({self.filename}) by {self.uploaded_by.username}"


class Directory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="directories")
    parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True, related_name="subdirectories")
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    @property
    def path(self):
        if self.parent:
            return f"{self.parent.path}/{self.name}"
        return self.name

    def __str__(self):
        return f"{self.name}"


class CloudFile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="files")
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    parent = models.ForeignKey(Directory, on_delete=models.CASCADE, null=True, blank=True, related_name="files")
    media = models.ForeignKey(MediaFile, on_delete=models.CASCADE, related_name="cloud_files", null=True, blank=True)

    def __str__(self):
        return f"{self.name}"


class SharedItem(models.Model):
    PERMISSION_CHOICES = (
        ("view", "View"),
        ("edit", "Edit"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="shared_items")
    content = models.ForeignKey(CloudFile, on_delete=models.CASCADE, null=True, blank=True, related_name="shared_with")
    directory = models.ForeignKey(Directory, on_delete=models.CASCADE, null=True, blank=True, related_name="shared_with")
    permission = models.CharField(max_length=10, choices=PERMISSION_CHOICES, default="view")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        shared_item = self.content.name if self.content else self.directory
        return f"{shared_item} shared with {self.user.email}"


class Tag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tags")
    related_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="related_tags")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Enforce unique constraint for tag name per owner
        # Also enforce unique constraint for related_user per owner
        constraints = [
            models.UniqueConstraint(fields=["owner", "name"], name="unique_tag_name_per_owner"),
            models.UniqueConstraint(
                fields=["owner", "related_user"],
                name="unique_related_user_per_owner",
                condition=models.Q(related_user__isnull=False),
            ),
        ]

    def __str__(self):
        if self.related_user:
            return f"{self.name} ({self.related_user.email})"
        return self.name


class FileTag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.ForeignKey(CloudFile, on_delete=models.CASCADE, related_name="tags")
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, related_name="files")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Ensure a file can't be tagged with the same tag multiple times
        constraints = [models.UniqueConstraint(fields=["file", "tag"], name="unique_file_tag")]

    def __str__(self):
        return f"{self.file.name} - {self.tag.name}"
