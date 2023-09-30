from django.db import models
from accounts.models import User

from base.models import Relationship

# Create your models here.


class Message(models.Model):
    room = models.ForeignKey(Relationship, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('date_added',)

    def __str__(self):
        return f'{self.user} - {self.content}'