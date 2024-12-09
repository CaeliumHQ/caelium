import json

import jwt
from channels.generic.websocket import WebsocketConsumer
from django.conf import settings
from asgiref.sync import async_to_sync

from accounts.models import User


class BaseConsumer(WebsocketConsumer):

    def connect(self):
        token = self.scope["url_route"]["kwargs"]["token"]
        try:
            decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user_id = decoded_token["user_id"]
            self.user = User.objects.get(id=user_id)
            self.accept()

            # Add the user to a group named after their user ID
            async_to_sync(self.channel_layer.group_add)(
                f"user_{user_id}",
                self.channel_name
            )

            self.send(text_data=json.dumps({"message": f"Welcome to Caelium, {self.user.username}!"}))
        except (jwt.ExpiredSignatureError, jwt.DecodeError, User.DoesNotExist):
            self.close()

    def disconnect(self, close_code):
        # Remove the user from their group on disconnect
        async_to_sync(self.channel_layer.group_discard)(
            f"user_{self.user.id}",
            self.channel_name
        )

    def receive(self, text_data):
        data = json.loads(text_data)
        message = data.get("message")
        receiver_id = data.get("receiver_id")


        if message and receiver_id:
            print(message, receiver_id)
            # Send the message to the receiver's group
            async_to_sync(self.channel_layer.group_send)(
                f"user_{receiver_id}",
                {
                    "type": "chat_message",
                    "message": message,
                    "sender": self.user.username
                }
            )

    def chat_message(self, event):
        message = event["message"]
        sender = event["sender"]

        # Send the message to WebSocket
        self.send(text_data=json.dumps({
            "message": message,
            "sender": sender
        }))
