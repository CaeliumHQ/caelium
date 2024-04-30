from django.db import models


class Chat(models.Model):
    name = models.CharField(max_length=30, null=True, blank=True)
    participants = models.ManyToManyField("accounts.User")
    updated_time = models.DateTimeField(auto_now=True)

    def __str__(self):
        participant_names = list(self.participants.values_list("username", flat=True))
        return f"{self.pk}: {', '.join(participant_names)}"


class Message(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE)
    sender = models.ForeignKey("accounts.User", on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    type = models.CharField(
        max_length=6,
        choices={
            "text": "text",
            "image": "image",
            "doc": "doc",
            "voice": "voice",
            "video": "video",
        },
    )
    content = models.TextField(null=True, blank=True)
    file = models.FileField(null=True, blank=True, upload_to='chats')

    def __str__(self) -> str:
        return f"{self.sender.username}: {self.content}"
