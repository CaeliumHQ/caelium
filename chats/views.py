from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

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



class StartChatView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request, *args, **kwargs):
        recipient_user_id = request.data.get('recipient_user_id')
        if not recipient_user_id:
            return Response({'error': 'recipient_user_id is required.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            recipient_user = User.objects.get(pk=recipient_user_id)
        except User.DoesNotExist:
            return Response({'error': 'Recipient user not found.'}, status=status.HTTP_404_NOT_FOUND)
        current_user = request.user
        chat, created = Chat.objects.get_or_create(participants__in=[current_user.id, recipient_user.id], is_group=False)

        if created:
            # Optionally, you can send a welcome message or perform other actions here
            pass

        serializer = ChatSerializer(chat)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
