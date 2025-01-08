from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from accounts.serializers import UserSerializer
from base.utils import socket_notify_user

from .models import Call, Chat, Message
from .serializers import ChatSerializer, MessageCreateSerializer, MessageSerializer


class MessagePagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = "page_size"
    max_page_size = 100


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
        return Chat.objects.filter(participants=self.request.user).order_by("-updated_time")

    def destroy(self, request, *args, **kwargs):
        chat = self.get_object()
        if chat.is_group:
            if chat.creator == request.user:
                chat.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response({"error": "Only group creator can delete group chats"}, status=status.HTTP_403_FORBIDDEN)
        else:
            chat.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["get"])
    def messages(self, request, pk=None):
        chat = self.get_object()
        if request.user not in chat.participants.all():
            return Response({"error": "You are not a participant of this chat"}, status=status.HTTP_403_FORBIDDEN)
        messages = chat.message_set.all().order_by("-timestamp")
        page = self.paginate_queryset(messages)
        serializer = MessageSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=False, methods=["get"])
    def users(self, request):
        current_user = request.user
        existing_chat_users = User.objects.filter(
            chat__participants=current_user, is_active=True  # Only get active users
        ).distinct()
        new_users = (
            User.objects.filter(is_active=True)  # Only get active users
            .exclude(id__in=existing_chat_users)
            .exclude(id=current_user.id)
        )

        serializer = UserSerializer(new_users, many=True)
        return Response(serializer.data)


class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    queryset = Message.objects.all()
    pagination_class = MessagePagination
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "create":
            return MessageCreateSerializer
        return MessageSerializer

    def get_queryset(self):
        chat_id = self.kwargs.get("chat_id")
        # Check if user is participant of the chat
        chat = Chat.objects.filter(id=chat_id, participants=self.request.user).first()
        if not chat:
            return Message.objects.none()
        return Message.objects.filter(chat_id=chat_id).order_by("-timestamp")


class ChatUsers(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return User.objects.filter(is_active=True).exclude(id=self.request.user.id).order_by("name")


class InitiateCallAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        chat_id = request.data.get("chat_id")
        call_type = request.data.get("call_type")  # "audio" or "video"

        # Fetch chat and ensure the user is a participant
        chat = Chat.objects.get(id=chat_id, participants=request.user)

        # Create a Call instance
        call = Call.objects.create(
            chat=chat,
            call_type=call_type,
            initiator=request.user,
        )

        for participant in chat.participants.all():
            socket_notify_user(
                participant,
                "call_invitation",
                {
                    "chat_id": chat.id,
                    "call_id": call.id,
                    "call_type": call_type,
                    "initiator": request.user.username,
                },
            )
        return Response({"message": "Call initiated successfully", "call_id": call.id})
