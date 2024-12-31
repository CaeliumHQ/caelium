from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.models import User
from accounts.serializers import UserSerializer

from .models import Chat, Message
from .serializers import ChatSerializer, GroupChatSerializer, MessageCreateSerializer, MessageSerializer


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
    
    @action(detail=True, methods=["delete"])
    def delete_chat(self, request, *args, **kwargs):
        chat = self.get_object()
        if chat.is_group and chat.creator == request.user:
            chat.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({"error": "You are not authorized to delete this chat"}, status=status.HTTP_403_FORBIDDEN)

    @action(detail=False, methods=["post"])
    def create_group(self, request):
        serializer = GroupChatSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            chat = serializer.save()
            return Response(ChatSerializer(chat, context={"request": request}).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
        if Chat.objects.filter(id=chat_id, participants=self.request.user).exists():
            return Message.objects.filter(chat_id=chat_id).order_by("-id")
        return Message.objects.none()


class ChatUsers(viewsets.ModelViewSet):
    serializer_class = UserSerializer

    def get_queryset(self):
        return User.objects.all().exclude(email=self.request.user.email)
