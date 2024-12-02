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
            user = User.objects.get(id=user_id)
            if user.email == "admin@jerit.in":
                self.accept()
                # Add admin to a group for broadcasting
                async_to_sync(self.channel_layer.group_add)("admin_group", self.channel_name)
                self.send(text_data=json.dumps({"message": f"Welcome on Board admin, {user.username}!"}))
            else:
                self.close(code=4003)

        except jwt.ExpiredSignatureError:
            self.close(code=4001)
        except jwt.DecodeError:
            self.close(code=4002)
        except User.DoesNotExist:
            self.close(code=4004)

    def disconnect(self, close_code):
        if hasattr(self, 'user') and self.user.email == "admin@jerit.in":
            async_to_sync(self.channel_layer.group_discard)("admin_group", self.channel_name)

    def receive(self, text_data):
        pass

    def log_entry(self, event):
        self.send(text_data=json.dumps(event))
