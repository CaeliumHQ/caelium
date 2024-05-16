from django.db import models


# Create your models here.
class Album(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class MediaFile(models.Model):
    PHOTO = "photo"
    VIDEO = "video"
    MEDIA_TYPES = [
        (PHOTO, "Photo"),
        (VIDEO, "Video"),
    ]

    album = models.ManyToManyField(Album, related_name="media_files")
    file = models.FileField(upload_to="media/")
    timestamp = models.DateTimeField()
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPES)

    def __str__(self):
        return f"{self.file.name} - {self.timestamp}"
