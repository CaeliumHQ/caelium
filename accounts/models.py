from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError("The given email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    GENDER_CHOICES = [
        ("Male", "Male"),
        ("Female", "Female"),
        ("Other", "Other"),
    ]
    username = None
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=24)
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
    password = models.CharField(null=True, blank=True, max_length=255)
    objects = UserManager()
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return f"{self.email}"


class GoogleToken(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    access_token = models.CharField(max_length=255)
    refresh_token = models.CharField(max_length=255)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"GoogleToken for {self.user.email}"
