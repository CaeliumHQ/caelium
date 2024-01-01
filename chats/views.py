from rest_framework import generics, status, viewsets
from rest_framework.response import Response

from .models import Chat, Message
from .serializers import ChatSerializer, MessageSerializer


class ChatViewSet(viewsets.ModelViewSet):
    serializer_class = ChatSerializer
    def get_queryset(self):
        user = self.request.user
        return Chat.objects.filter(participants=user)

class MessageCreateView(generics.CreateAPIView):
    serializer_class = MessageSerializer
    queryset = Message.objects.all()

class ChatCreateView(generics.CreateAPIView):
    serializer_class = ChatSerializer
    queryset = Chat.objects.all()

class MessagesView(generics.ListAPIView):
    serializer_class = MessageSerializer

    def get_queryset(self):
        chat_id = self.kwargs['pk']
        try:
            # Assuming 'chat_id' is the primary key of the Chat model
            chat_messages = Message.objects.filter(chat=Chat.objects.get(id=chat_id))
            return chat_messages
        except Message.DoesNotExist:
            return []

    def list(self, request, *args, **kwargs):
        chat_id = self.kwargs['pk']
        queryset = self.get_queryset()
        if not queryset:
            return Response({"message": f"Chat with id {chat_id} not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
