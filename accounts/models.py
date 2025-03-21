from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):

    use_in_migrations = True

    def _create_user(self, email, password, username, **extra_fields):
        """Create and save a User with the given email, password, and username."""
        if not email:
            raise ValueError("The given email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, username=None, **extra_fields):
        """Create and save a regular User with the given email, password, and username."""
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, username, **extra_fields)

    def create_superuser(self, email, password, username=None, **extra_fields):
        """Create and save a SuperUser with the given email, password, and username."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, username, **extra_fields)


class User(AbstractUser):
    GENDER_CHOICES = [
        ("Male", "Male"),
        ("Female", "Female"),
        ("Other", "Other"),
    ]
    username = models.CharField(max_length=150, unique=True, null=True, blank=True)
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=24)
    avatar = models.ImageField(
        upload_to="avatars/",
        default="defaults/avatar.png",
        null=True,
        blank=True,
    )
    location = models.CharField(max_length=100, null=True, blank=True)
    gender = models.CharField(max_length=6, choices=GENDER_CHOICES, null=True, blank=True, default="Other")
    bio = models.TextField(null=True, blank=True)
    birthdate = models.DateField(null=True, blank=True)
    password = models.CharField(null=True, blank=True, max_length=255)
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(default=timezone.now, null=True, blank=True)
    objects = UserManager()

    USERNAME_FIELD = "username"  # Use username as the login field for Django
    REQUIRED_FIELDS = ["email"]  # Keep email in required fields for user creation

    def __str__(self):
        return f"{self.username} ({self.email})"

    def update_last_seen(self):
        self.last_seen = timezone.now()
        self.is_online = False
        self.save()


class GoogleToken(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    access_token = models.CharField(max_length=255)
    refresh_token = models.CharField(max_length=255)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"GoogleToken for {self.user.username}"


class FCMToken(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="fcm_token")
    token = models.CharField(max_length=255, unique=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - FCM Token"


class TestUserEmail(models.Model):
    email = models.EmailField(unique=True)
    added_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-added_at"]

    def __str__(self):
        status = "active" if self.is_active else "inactive"
        return f"{self.email} ({status})"

    @classmethod
    def is_allowed_test_email(cls, email):
        return cls.objects.filter(email=email, is_active=True).exists()


class SpecialUser(models.Model):
    """Model to track special user emails for providing exclusive features and access"""

    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    added_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-added_at"]

    def __str__(self):
        return f"{self.name} ({self.email}) - Special User"

    @classmethod
    def is_special_user(cls, email):
        """Check if an email belongs to a special user"""
        return cls.objects.filter(email=email, is_active=True).exists()
