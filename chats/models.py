from django.db import models
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.utils import timezone

from accounts.models import User


class Chat(models.Model):
    name = models.CharField(max_length=30, null=True, blank=True)
    participants = models.ManyToManyField("accounts.User", related_name="chats")
    updated_time = models.DateTimeField(auto_now=True)
    is_group = models.BooleanField(default=False)
    group_icon = models.ImageField(null=True, blank=True, upload_to="group_icons")
    creator = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, null=True, blank=True, related_name="created_chats"
    )
    latest_call = models.ForeignKey(
        "Call", on_delete=models.SET_NULL, null=True, blank=True, related_name="chat_latest_call"
    )

    def __str__(self):
        participant_names = list(self.participants.values_list("name", flat=True))
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
        return f"{self.sender.name}: {self.content}"


class Call(models.Model):
    CALL_TYPES = [
        ("audio", "Audio"),
        ("video", "Video"),
    ]
    chat = models.ForeignKey("Chat", on_delete=models.CASCADE, related_name="calls")
    call_type = models.CharField(max_length=10, choices=CALL_TYPES)
    started_at = models.DateTimeField(default=timezone.now)
    ended_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ("ongoing", "Ongoing"),
            ("ended", "Ended"),
            ("missed", "Missed"),
        ],
        default="ongoing",
    )
    initiator = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="initiated_calls")

    def end_call(self):
        self.ended_at = timezone.now()
        self.status = "ended"
        self.save()

    def __str__(self):
        return f"{self.call_type.capitalize()} call in {self.chat.name} - {self.status}"


class CallParticipant(models.Model):
    call = models.ForeignKey("Call", on_delete=models.CASCADE, related_name="participants")
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE)
    joined_at = models.DateTimeField(null=True, blank=True)
    left_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ("invited", "Invited"),
            ("joined", "Joined"),
            ("declined", "Declined"),
        ],
        default="invited",
    )

    def __str__(self):
        return f"{self.user.username} - {self.status} in call {self.call.id}"


@receiver(post_save, sender=Call)
def create_call_participants(sender, instance, created, **kwargs):
    if created:
        for participant in instance.chat.participants.all():
            CallParticipant.objects.create(call=instance, user=participant)
