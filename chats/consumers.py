import json

import jwt
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from django.conf import settings

from accounts.models import User


class CallConsumer(WebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.chat_id = None
        self.user = None

    def connect(self):
        self.chat_id = self.scope["url_route"]["kwargs"]["chat_id"]
        self.user = self.authenticate_user()

        if not self.user:
            self.close()
            return

        # Ensure user is a participant of the chat
        if not self.user.chats.filter(id=self.chat_id).exists():
            self.close()
            return

        async_to_sync(self.channel_layer.group_add)(f"chat_{self.chat_id}", self.channel_name)
        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(f"chat_{self.chat_id}", self.channel_name)

    def receive(self, text_data):
        data = json.loads(text_data)

        # Example event handling
        if data["type"] == "call_initiate":
            async_to_sync(self.channel_layer.group_send)(
                f"chat_{self.chat_id}",
                {
                    "type": "call.initiate",
                    "caller": self.user.username,
                },
            )
        elif data["type"] == "sdp_offer":
            async_to_sync(self.channel_layer.group_send)(
                f"chat_{self.chat_id}",
                {
                    "type": "sdp.offer",
                    "offer": data["offer"],
                    "sender": self.user.username,
                },
            )
        elif data["type"] == "sdp_answer":
            async_to_sync(self.channel_layer.group_send)(
                f"chat_{self.chat_id}",
                {
                    "type": "sdp.answer",
                    "answer": data["answer"],
                    "sender": self.user.username,
                },
            )
        elif data["type"] == "ice_candidate":
            async_to_sync(self.channel_layer.group_send)(
                f"chat_{self.chat_id}",
                {
                    "type": "ice.candidate",
                    "candidate": data["candidate"],
                    "sender": self.user.username,
                },
            )
        elif data["type"] == "call_end":
            async_to_sync(self.channel_layer.group_send)(
                f"chat_{self.chat_id}",
                {
                    "type": "call.end",
                    "message": f"{self.user.username} ended the call",
                },
            )

    # Event Handlers for WebSocket Group
    def call_initiate(self, event):
        self.send(text_data=json.dumps({"type": "call_initiate", "caller": event["caller"]}))

    def sdp_offer(self, event):
        self.send(text_data=json.dumps({"type": "sdp_offer", "offer": event["offer"], "sender": event["sender"]}))

    def sdp_answer(self, event):
        self.send(text_data=json.dumps({"type": "sdp_answer", "answer": event["answer"], "sender": event["sender"]}))

    def ice_candidate(self, event):
        self.send(
            text_data=json.dumps({"type": "ice_candidate", "candidate": event["candidate"], "sender": event["sender"]})
        )

    def call_end(self, event):
        self.send(text_data=json.dumps({"type": "call_end", "message": event["message"]}))

    def authenticate_user(self):
        token = self.scope["query_string"].decode("utf-8").split("=")[-1]
        try:
            decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            return User.objects.get(id=decoded_token["user_id"])
        except (jwt.ExpiredSignatureError, jwt.DecodeError, User.DoesNotExist):
            return None
