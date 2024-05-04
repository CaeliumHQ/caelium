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
    members = models.ManyToManyField(User)

    class Meta:
        verbose_name_plural = "Families"


class Work(models.Model):
    members = models.ManyToManyField(User)


class JoinSpaceRequest(models.Model):
    space = models.CharField(max_length=25, choices=SPACES)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    confirmed = models.BooleanField(default=False)


class Task(models.Model):
    name = models.CharField(max_length=255)
    space = models.CharField(
        max_length=255,
        choices=(
            ("personal", "Personal"),
            ("partner", "Partner"),
            ("family", "Family"),
        ),
    )
    completed = models.BooleanField(default=False)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.owner} - {self.name}"