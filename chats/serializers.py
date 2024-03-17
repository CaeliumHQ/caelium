# serializers.py

from rest_framework import serializers

from accounts.serializers import UserSerializer

from .models import Chat, Message


class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer()

    class Meta:
        model = Message
        fields = ('id', 'sender', 'timestamp', 'content')
class ChatSerializer(serializers.ModelSerializer):
    other_participant = serializers.SerializerMethodField()
    last_message_content = serializers.SerializerMethodField()
    last_message_time = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = ('id', 'other_participant', 'last_message_content', 'last_message_time')

    def get_other_participant(self, obj):
        user = self.context['request'].user
        participants = obj.participants.exclude(id=user.id)
        if participants.exists():
            return UserSerializer(participants.first()).data
        return None

    def get_last_message_content(self, obj):
        last_message = obj.message_set.last()
        if last_message:
            return last_message.content
        return None

    def get_last_message_time(self, obj):
        last_message = obj.message_set.last()
        if last_message:
            return last_message.timestamp
        return None


class CreateMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ('content',)

class CreateChatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chat
        fields = ('participants',)
