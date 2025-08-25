from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.cache import cache
from django.core.exceptions import ValidationError
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

    def get_followers_count(self):
        """Get the number of followers for this user"""
        # Use cache if available, fallback to database count
        cache_key = f"user_{self.id}_followers_count"

        count = cache.get(cache_key)
        if count is None:
            count = self.followers.count()
            cache.set(cache_key, count, 300)  # Cache for 5 minutes
        return count

    def get_following_count(self):
        """Get the number of users this user is following"""
        # Use cache if available, fallback to database count
        cache_key = f"user_{self.id}_following_count"

        count = cache.get(cache_key)
        if count is None:
            count = self.following.count()
            cache.set(cache_key, count, 300)  # Cache for 5 minutes
        return count

    def is_following(self, user):
        """Check if this user is following another user"""
        # Use select_related to reduce queries if needed in bulk operations
        return self.following.filter(followed=user).exists()

    def is_followed_by(self, user):
        """Check if this user is followed by another user"""
        return self.followers.filter(follower=user).exists()

    def invalidate_follow_cache(self):
        """Invalidate cached follower/following counts"""

        cache.delete(f"user_{self.id}_followers_count")
        cache.delete(f"user_{self.id}_following_count")

    def get_mutual_followers_with(self, other_user):
        """Get mutual followers between this user and another user"""
        return Follow.get_mutual_followers(self, other_user)

    def get_follow_suggestions(self, limit=10):
        """Get follow suggestions for this user"""
        return Follow.get_follow_suggestions(self, limit)

    def bulk_follow_check(self, user_ids):
        """Check if this user is following multiple users at once"""
        if not user_ids:
            return {}

        following_ids = set(self.following.filter(followed_id__in=user_ids).values_list("followed_id", flat=True))

        return {user_id: user_id in following_ids for user_id in user_ids}


class Follow(models.Model):
    """
    Model to handle following relationships between users.
    Optimized for fast queries with proper indexing.
    Instagram-style following system with performance optimizations.
    """

    follower = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="following", help_text="The user who is following"
    )
    followed = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="followers", help_text="The user being followed"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Ensure a user can't follow the same person twice
        unique_together = ("follower", "followed")
        # Add database indexes for fast queries
        indexes = [
            models.Index(fields=["follower"]),
            models.Index(fields=["followed"]),
            models.Index(fields=["follower", "followed"]),
            models.Index(fields=["created_at"]),
            # Additional indexes for common query patterns
            models.Index(fields=["-created_at"]),  # For recent follows
            models.Index(fields=["followed", "-created_at"]),  # For user's recent followers
            models.Index(fields=["follower", "-created_at"]),  # For user's recent following
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.follower.username} follows {self.followed.username}"

    def clean(self):
        """Prevent users from following themselves"""

        if self.follower == self.followed:
            raise ValidationError("Users cannot follow themselves")

    @classmethod
    def get_mutual_followers(cls, user1, user2):
        """Get users that both user1 and user2 follow (mutual connections)"""
        user1_following = set(cls.objects.filter(follower=user1).values_list("followed_id", flat=True))
        user2_following = set(cls.objects.filter(follower=user2).values_list("followed_id", flat=True))
        mutual_ids = user1_following.intersection(user2_following)
        return User.objects.filter(id__in=mutual_ids)

    @classmethod
    def get_follow_suggestions(cls, user, limit=10):
        """Get follow suggestions based on mutual connections"""
        # Get users followed by people the current user follows
        following_ids = cls.objects.filter(follower=user).values_list("followed_id", flat=True)

        # Get suggestions from second-degree connections
        suggested_ids = (
            cls.objects.filter(follower_id__in=following_ids)
            .exclude(followed=user)  # Don't suggest the user themselves
            .exclude(followed_id__in=following_ids)  # Don't suggest already followed users
            .values_list("followed_id", flat=True)
            .distinct()[: limit * 2]
        )  # Get more than needed for filtering

        return User.objects.filter(id__in=suggested_ids)[:limit]

    def save(self, *args, **kwargs):
        self.clean()
        is_new = self.pk is None
        super().save(*args, **kwargs)

        # Invalidate cache after creating/updating follow relationship
        if is_new:
            self.follower.invalidate_follow_cache()
            self.followed.invalidate_follow_cache()

    def delete(self, *args, **kwargs):
        # Store references before deletion
        follower = self.follower
        followed = self.followed
        result = super().delete(*args, **kwargs)

        # Invalidate cache after deletion
        follower.invalidate_follow_cache()
        followed.invalidate_follow_cache()
        return result


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
