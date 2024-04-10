import json

from rest_framework import status, viewsets, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Chat, Message
from .serializers import ChatSerializer, MessageCreateSerializer, MessageSerializer


class ChatViewSet(viewsets.ModelViewSet):
    queryset = Chat.objects.all()
    serializer_class = ChatSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ["participants__name"]

    def create(self, request, *args, **kwargs):
        serializer = ChatSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_queryset(self):
        return Chat.objects.filter(participants=self.request.user).order_by(
            "-updated_time"
        )


class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    queryset = Message.objects.all()

    def get_serializer_class(self):
        if self.action == "create":
            return MessageCreateSerializer
        return MessageSerializer

    def create(self, *args, **kwargs):
        return Response(
            json.dumps({"error": "Messages can only be saved using the chat socket"}),
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def get_queryset(self):
        chat_id = self.kwargs.get("chat_id")
        if Chat.objects.filter(id=chat_id, participants=self.request.user):
            return Message.objects.filter(chat_id=chat_id)
