from django.db import models

from accounts.models import User
from base.models import SPACES

# Create your models here.


class Craft(models.Model):
    title = models.CharField(max_length=50)
    tag = models.CharField(max_length=25)
    banner = models.ImageField(upload_to="media/crafts/banners")
    content = models.TextField()
    date = models.DateTimeField()
    space = models.CharField(max_length=10, choices=SPACES)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
