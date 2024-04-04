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
