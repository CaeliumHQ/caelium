from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Chat, Message
from .serializers import (ChatSerializer, MessageCreateSerializer,
                          MessageSerializer)


class ChatViewSet(viewsets.ModelViewSet):
    queryset = Chat.objects.all()
    serializer_class = ChatSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = ChatSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUuEST)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"message": "Item deleted successfully"}, status=status.HTTP_200_OK
        )

    def get_queryset(self):
        return Chat.objects.filter(participants=self.request.user)


class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    queryset = Message.objects.all()

    def get_serializer_class(self):
        if self.action == "create":
            return MessageCreateSerializer
        return MessageSerializer

    def create(self, request, *args, **kwargs):
        chat_id = kwargs.get("chat_id")
        sender = request.user
        content = request.data.get("content")

        try:
            chat = Chat.objects.get(pk=chat_id)
        except Chat.DoesNotExist:
            return Response(
                {"error": "Chat not found"}, status=status.HTTP_404_NOT_FOUND
            )

        if sender not in chat.participants.all():
            return Response(
                {"error": "User is not a participant of this chat"},
                status=status.HTTP_403_FORBIDDEN,
            )

        data = {"chat": chat_id, "sender": sender.id, "content": content}
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save(chat_id=chat_id)  # Ensure chat_id is set when saving

        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def get_queryset(self):
        chat_id = self.kwargs.get("chat_id")
        if Chat.objects.filter(id=chat_id, participants=self.request.user):
            return Message.objects.filter(chat_id=chat_id)
