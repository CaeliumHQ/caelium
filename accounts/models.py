from django.contrib.auth.models import AbstractUser
from django.core.validators import MinLengthValidator
from django.db import models


class User(AbstractUser):
    GENDER_CHOICES = [
        ("Male", "Male"),
        ("Female", "Female"),
        ("Other", "Other"),
    ]
    username = models.CharField(
        max_length=50,
        unique=True,
        validators=[
            MinLengthValidator(
                limit_value=3, message="Username must be at least 4 characters long"
            )
        ],
    )
    name = models.CharField(max_length=30)
    avatar = models.ImageField(
        upload_to="avatars/",
        default="defaults/avatar.png",
        null=True,
        blank=True,
    )
    location = models.CharField(max_length=100, null=True, blank=True)
    gender = models.CharField(
        max_length=6, choices=GENDER_CHOICES, null=True, blank=True, default="Other"
    )
    bio = models.TextField(null=True, blank=True)
    birthdate = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.id}. {self.username}"
