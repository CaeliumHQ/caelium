from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, viewsets

from .models import Chat, Message
from .serializers import ChatSerializer, MessageSerializer

User = get_user_model()

class ChatViewSet(viewsets.ModelViewSet):
    serializer_class = ChatSerializer
    def get_queryset(self):
        user = self.request.user
        return Chat.objects.filter(participants=user)

class MessageCreateView(generics.CreateAPIView):
    serializer_class = MessageSerializer
    queryset = Message.objects.all()

class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    queryset = Message.objects.all()
    permission_classes = [permissions.IsAuthenticated]
