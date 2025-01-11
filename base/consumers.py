import json
import os

import jwt
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from django.conf import settings
from django.utils import timezone

from accounts.models import User
from accounts.serializers import UserSerializer
from chats.models import Chat, Message


class BaseConsumer(WebsocketConsumer):
    active_connections = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None

    def connect(self):
        token = self.scope["url_route"]["kwargs"]["token"]
        try:
            decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user_id = decoded_token["user_id"]
            self.user = User.objects.get(id=user_id)
            self.user.is_online = True
            self.user.save()
            self.accept()

            # Add connection to tracking
            if user_id not in self.active_connections:
                self.active_connections[user_id] = set()
            self.active_connections[user_id].add(self.channel_name)

            self.broadcast_status(is_online=True)
            async_to_sync(self.channel_layer.group_add)(f"user_{user_id}", self.channel_name)
            self.send(text_data=json.dumps({"message": f"Welcome to Caelium, {self.user.username}!"}))
            online_users = self.get_online_users()
            self.send(
                text_data=json.dumps(
                    {
                        "category": "online_users",
                        "online_users": online_users,
                    }
                )
            )
        except (jwt.ExpiredSignatureError, jwt.DecodeError, User.DoesNotExist):
            self.close()

    def has_other_connections(self):
        if self.user.id not in self.active_connections:
            return False
        connections = self.active_connections[self.user.id]
        connections.discard(self.channel_name)
        return bool(connections)

    def disconnect(self, close_code):
        if self.user:
            if self.user.id in self.active_connections:
                self.active_connections[self.user.id].discard(self.channel_name)
                if not self.active_connections[self.user.id]:
                    del self.active_connections[self.user.id]
                    self.user.update_last_seen()
                    self.broadcast_status(is_online=False)
            async_to_sync(self.channel_layer.group_discard)(f"user_{self.user.id}", self.channel_name)

    def receive(self, text_data):
        try:
            data = json.loads(text_data)
            if data["category"] == "text_message":
                message = Message.objects.create(
                    chat_id=data["chat_id"],
                    sender=self.user,
                    content=data["message"],
                    type="txt",
                )
                chat = Chat.objects.get(id=data["chat_id"])
                chat.updated_time = timezone.now()
                chat.save()
                if message:
                    for recipient in Chat.objects.get(id=data["chat_id"]).participants.all():
                        async_to_sync(self.channel_layer.group_send)(
                            f"user_{recipient.id}",
                            {"type": "new_message", "message": message},
                        )

            elif data["category"] == "file_message":
                message = Message.objects.get(id=data["message_id"])
                for recipient in Chat.objects.get(id=data["chat_id"]).participants.all():
                    if recipient.id is not self.user.id:
                        async_to_sync(self.channel_layer.group_send)(
                            f"user_{recipient.id}", {"type": "new_message", "message": message}
                        )
            elif data["category"] == "typing":
                chat = Chat.objects.get(id=data["chat_id"])
                data["sender"] = self.user.id
                for recipient in chat.participants.all():
                    if recipient.id is not self.user.id:
                        async_to_sync(self.channel_layer.group_send)(
                            f"user_{recipient.id}", {"type": "typing", "data": data}
                        )
            elif data["category"] == "incoming_call":
                chat = Chat.objects.get(id=data["chat_id"])
                data["caller"] = UserSerializer(self.user).data
                for recipient in chat.participants.all():
                    if recipient.id != self.user.id:
                        async_to_sync(self.channel_layer.group_send)(
                            f"user_{recipient.id}", {"type": "incoming_call", "data": data}
                        )

        except (json.JSONDecodeError, Message.DoesNotExist, Chat.DoesNotExist, KeyError) as e:
            print(" Error:", e)

    def incoming_call(self, event):
        self.send(text_data=json.dumps(event["data"]))

    def new_message(self, event):
        message = event["message"]
        self.send(
            text_data=json.dumps(
                {
                    "category": "new_message",
                    "type": message.type,
                    "id": message.id,
                    "chat": message.chat.id,
                    "content": message.content,
                    "sender": message.sender.id,
                    "timestamp": str(message.timestamp),
                    "file": f"{os.environ['SERVER_HOST']}{message.file.url}" if message.file else None,
                }
            )
        )

    def typing(self, event):
        self.send(text_data=json.dumps(event["data"]))

    def broadcast_status(self, is_online):
        status_data = {
            "type": "user_status_change",
            "user_id": self.user.id,
            "is_online": is_online,
            "last_seen": str(self.user.last_seen),
        }
        for chat in self.user.chats.all():
            for participant in chat.participants.all():
                if participant != self.user:
                    async_to_sync(self.channel_layer.group_send)(f"user_{participant.id}", status_data)

    def user_status_change(self, event):
        self.send(
            text_data=json.dumps(
                {
                    "category": "status_update",
                    "user_id": event["user_id"],
                    "is_online": event["is_online"],
                    "last_seen": event["last_seen"],
                }
            )
        )

    def get_online_users(self):
        online_users = set()  # Using set to avoid duplicates
        for chat in self.user.chats.all():
            for participant in chat.participants.all():
                if participant.is_online and participant.id != self.user.id:
                    online_users.add(participant.id)
        return list(online_users)
