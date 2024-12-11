import json

import jwt
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from django.conf import settings

from accounts.models import User
from chats.models import Chat, Message


class BaseConsumer(WebsocketConsumer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None

    def connect(self):
        token = self.scope["url_route"]["kwargs"]["token"]
        try:
            decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user_id = decoded_token["user_id"]
            self.user = User.objects.get(id=user_id)
            self.accept()

            # Add the user to a group named after their user ID
            async_to_sync(self.channel_layer.group_add)(f"user_{user_id}", self.channel_name)

            self.send(text_data=json.dumps({"message": f"Welcome to Caelium, {self.user.username}!"}))
        except (jwt.ExpiredSignatureError, jwt.DecodeError, User.DoesNotExist):
            self.close()

    def disconnect(self, close_code):
        # Remove the user from their group on disconnect
        async_to_sync(self.channel_layer.group_discard)(f"user_{self.user.id}", self.channel_name)

    def receive(self, text_data):
        data = json.loads(text_data)
        message = Message.objects.create(chat_id=data["chat_id"], sender=self.user, content=data["message"], type="txt")
        if message:
            for recipient in Chat.objects.get(id=data["chat_id"]).participants.all():
                if recipient.id is not self.user.id:
                    async_to_sync(self.channel_layer.group_send)(
                        f"user_{recipient.id}",
                        {"type": "chat_message", "message": message},
                    )

    def chat_message(self, event):
        message = event["message"]
        self.send(
            text_data=json.dumps(
                {
                    "category": "message",
                    "type": message.type,
                    "id": message.id,
                    "chat_id": message.chat.id,
                    "content": message.content,
                    "sender": message.sender.id,
                    "timestamp": str(message.timestamp),
                }
            )
        )
