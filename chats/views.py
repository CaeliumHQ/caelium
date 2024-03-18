from rest_framework import generics

from accounts.serializers import UserSerializer

from .models import Chat, Message
from .serializers import (ChatSerializer, CreateChatSerializer,
                          CreateMessageSerializer, MessageSerializer)


class ChatListView(generics.ListAPIView):
    serializer_class = ChatSerializer

    def get_queryset(self):
        user = self.request.user
        return Chat.objects.filter(participants=user)

class ChatParticipantAPIView(generics.RetrieveAPIView):
    serializer_class = UserSerializer

    def get_object(self):
        chat_id = self.kwargs['chat_id']
        requested_user = self.request.user
        try:
            chat = Chat.objects.get(id=chat_id)
            if requested_user in chat.participants.all():  # Ensure requested user is a participant
                other_participant = chat.participants.exclude(id=requested_user.id).first()
                return other_participant
            return None  # Return None if the requested user is not a participant
        except Chat.DoesNotExist:
            return None

class ChatMessageListView(generics.ListAPIView):
    serializer_class = MessageSerializer

    def get_queryset(self):
        chat_id = self.kwargs['chat_id']
        return Message.objects.filter(chat_id=chat_id)

class CreateMessageAPIView(generics.CreateAPIView):
    serializer_class = CreateMessageSerializer

    def perform_create(self, serializer):
        sender = self.request.user
        serializer.save(sender=sender)

class CreateChatAPIView(generics.CreateAPIView):
    serializer_class = CreateChatSerializer

    def perform_create(self, serializer):
        participant = self.request.user
        other_participant_id = self.request.data.get('participant')
        if other_participant_id:
            chat = Chat.objects.create()
            chat.participants.add(participant, other_participant_id)
            serializer.save(chat=chat)
