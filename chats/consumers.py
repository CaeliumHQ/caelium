import json

import jwt
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from django.conf import settings

from accounts.models import User


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

    def receive(self, text_data=None):
        try:
            message_data = json.loads(text_data)
            message_id = message_data.get("message_id")
            message = {
                "message_id": message_id,
            }
            async_to_sync(self.channel_layer.group_send)(
                self.group_name, {"type": "chat_message", "message": message}
            )
        except Exception as e:
            print("Error processing message: ", e)

    def chat_message(self, event):
        message = event["message"]
        self.send(text_data=json.dumps({"type": "chat", "message": message}))
