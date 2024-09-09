from django.db import models
from django.utils import timezone

from accounts.models import User
from base.models import SPACES

# Create your models here.


class Craft(models.Model):
    title = models.CharField(max_length=50)
    tag = models.CharField(max_length=25)
    banner = models.ImageField(upload_to="crafts/banners")
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)  # Default value set during creation
    space = models.CharField(max_length=10, choices=SPACES)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.owner} - {self.title}"
