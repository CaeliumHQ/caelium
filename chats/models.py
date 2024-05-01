from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from accounts.models import User


class Chat(models.Model):
    name = models.CharField(max_length=30, null=True, blank=True)
    participants = models.ManyToManyField("accounts.User")
    updated_time = models.DateTimeField(auto_now=True)

    def __str__(self):
        participant_names = list(self.participants.values_list("username", flat=True))
        return f"{self.pk}: {', '.join(participant_names)}"


@receiver(pre_delete, sender=User)
def delete_chats_on_user_delete(sender, instance, **kwargs):
    # Delete all chats where the user is a participant
    Chat.objects.filter(participants=instance).delete()


class Message(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE)
    sender = models.ForeignKey("accounts.User", on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    type = models.CharField(
        max_length=6,
        choices={
            "txt": "txt",
            "img": "img",
            "doc": "doc",
            "aud": "aud",
            "vid": "vid",
        },
    )
    content = models.TextField(null=True, blank=True)
    file = models.FileField(null=True, blank=True, upload_to="chats")

    def __str__(self) -> str:
        return f"{self.sender.username}: {self.content}"
