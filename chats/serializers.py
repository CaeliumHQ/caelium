from rest_framework import serializers

from accounts.models import User
from accounts.serializers import UserSerializer

from .models import Chat, Message


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
            if last_message.sender == self.context['request'].user:
                return f"You: {last_message.content}"
            return f"{last_message.sender.name}: {last_message.content}"
        return None

    def get_last_message_time(self, obj):
        last_message = obj.message_set.last()
        if last_message:
            return last_message.timestamp
        return None

    def create(self, validated_data):
        current_user = self.context['request'].user
        participant_id = self.context['request'].data.get('participant')
        if not participant_id:
            raise serializers.ValidationError("Participant ID is required")
        try:
            participant = User.objects.get(pk=participant_id)
        except User.DoesNotExist as exc:
            raise serializers.ValidationError("Participant does not exist") from exc
        if Chat.objects.filter(participants=current_user).filter(participants=participant_id).exists():
            raise serializers.ValidationError("Chat already exists with same participants")
        chat = Chat.objects.create()
        chat.participants.add(current_user, participant)
        return chat

class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer()
    chat = ChatSerializer()
    class Meta:
        model = Message
        fields = '__all__'
