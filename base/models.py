from django.db import models

from accounts.models import User

SPACES = (
    ("personal", "Personal"),
    ("partner", "Partner"),
    ("family", "Family"),
    ("all", "All"),
)


class Couple(models.Model):
    members = models.ManyToManyField(User)
    anniversary = models.DateTimeField()


class Family(models.Model):
    name = models.CharField(max_length=100, null=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="families", null=True)
    tasks = models.ManyToManyField('base.Task', blank=True)

    class Meta:
        verbose_name_plural = "Families"
        
    def __str__(self):
        return f"{self.name} House"


class Member(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    family = models.ForeignKey(Family, on_delete=models.CASCADE)
    role = models.CharField(
        max_length=20, choices=[("parent", "Parent"), ("child", "Child")]
    )


class Work(models.Model):
    members = models.ManyToManyField(User)


class JoinSpaceRequest(models.Model):
    space = models.CharField(max_length=25, choices=SPACES)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    confirmed = models.BooleanField(default=False)


class Task(models.Model):
    name = models.CharField(max_length=255)
    completed = models.BooleanField(default=False)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    space = models.CharField(
        max_length=255,
        choices=(
            ("personal", "Personal"),
            ("partner", "Partner"),
            ("family", "Family"),
        ),
    )

    def __str__(self):
        return f"{self.owner} - {self.name}"


class Event(models.Model):
    name = models.CharField(max_length=255)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    all_day = models.BooleanField(default=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    description = models.TextField(blank=True, null=True)
    space = models.CharField(
        max_length=255,
        choices=(
            ("personal", "Personal"),
            ("partner", "Partner"),
            ("family", "Family"),
        ),
    )
