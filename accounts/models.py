from django.contrib.auth.models import AbstractUser
from django.core.validators import MinLengthValidator
from django.db import models


class User(AbstractUser):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    username = models.CharField(
        max_length=50,
        unique=True,
        validators=[MinLengthValidator(limit_value=4, message='Username must be at least 4 characters long')],
    )
    name = models.CharField(max_length=30)
    avatar = models.ImageField(upload_to='avatars/', default='media/avatars/default.png', null=True, blank=True)
    location = models.CharField(max_length=100, null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True, blank=True, default='Other')
    bio = models.TextField(null=True, blank=True)
    birthdate = models.DateField(null=True, blank=True)

    def __str__(self):
        return str(self.username)
