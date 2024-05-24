from django.db import models

from accounts.models import User


# Create your models here.
class Album(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return str(self.name)


class MediaFile(models.Model):
    PHOTO = "photo"
    VIDEO = "video"
    MEDIA_TYPES = [
        (PHOTO, "Photo"),
        (VIDEO, "Video"),
    ]

    album = models.ManyToManyField(Album, related_name="media_files", blank=True)
    file = models.FileField(upload_to="gallery")
    timestamp = models.DateField()
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPES)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.file.name} - {self.timestamp}"
