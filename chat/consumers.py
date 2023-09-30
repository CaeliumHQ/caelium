import json

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from .models import Message


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = await self.get_room()
        self.room_group_name = f"chat_{self.room_name}"

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]
        user = self.scope['user']
        email = user.email
        await self.save_message(user, message)

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name, {"type": "chat.message", "message": message, "user": email}
        )

    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'message',
            'data': event['message'],
            'user': event['user']
        }))

    @sync_to_async
    def save_message(self, user, message):
        room = user.relationship()
        Message.objects.create(room=room, user=user, content=message)
    @sync_to_async
    def get_room(self):
        return self.scope['user'].relationship().room