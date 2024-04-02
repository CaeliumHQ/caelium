import json

import jwt
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from django.conf import settings
from django.utils import timezone

from accounts.models import User
from chats.serializers import MessageCreateSerializer


class ChatConsumer(WebsocketConsumer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.chat_id = None
        self.group_name = None
        self.user = None

    def connect(self):
        self.chat_id = self.scope["url_route"]["kwargs"]["chat_id"]
        self.group_name = self.chat_id
        token = self.scope["url_route"]["kwargs"]["token"]
        try:
            decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user_id = decoded_token["user_id"]
            self.user = User.objects.get(id=user_id)
            async_to_sync(self.channel_layer.group_add)(
                self.group_name, self.channel_name
            )
            self.accept()
        except jwt.ExpiredSignatureError:
            self.close()
        except jwt.DecodeError:
            self.close()
        except User.DoesNotExist:
            self.close()

    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        content = text_data_json.get("content")
        token = text_data_json.get("token")
        try:
            decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user_id = decoded_token["user_id"]
            user = User.objects.get(id=user_id)
        except Exception as e:
            print("Token authentication failed:", e)
            return
        data = {
            "chat": self.chat_id,
            "sender": user.id,
            "content": content,
        }
        create_serializer = MessageCreateSerializer(data=data)
        if create_serializer.is_valid():
            saved_message = create_serializer.save()
            # Update the updated_time field of the chat instance
            chat = saved_message.chat
            chat.updated_time = timezone.now()
            chat.save()
            message = {
                "message_id": saved_message.id,
                "user_id": saved_message.sender.id,
                "content": saved_message.content,
                "name": saved_message.sender.name,
                "timestamp": saved_message.timestamp.strftime("%Y-%m-%dT%H:%M:%S"),
                "avatar": saved_message.sender.avatar.url,
            }
            async_to_sync(self.channel_layer.group_send)(
                self.group_name, {"type": "chat_message", "message": message}
            )
        else:
            print(create_serializer.errors)

    def chat_message(self, event):
        message = event["message"]
        self.send(text_data=json.dumps({"type": "chat", "message": message}))
