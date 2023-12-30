import os

from accounts.serializers import UserSerializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .models import Chat, Message


class ChatSerializer(serializers.ModelSerializer):
    chat = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = ['chat']

    def get_chat(self, obj):
        requesting_user = self.context['request'].user
        participants_data = UserSerializer(obj.participants.all(), many=True).data
        others_data = [user_data for user_data in participants_data if user_data['id'] != requesting_user.id]
        avatar = others_data[0]['avatar']
        name = others_data[0]['name']
        chat_id = obj.id
        return {'id': chat_id, 'avatar': os.environ['absolute_url'] + str(avatar), 'name': name}

    def create(self, validated_data):
        return Message.objects.create(**validated_data)



class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = '__all__'

    def validate_sender(self, value):
        chat = self.context['view'].kwargs.get('chat')  # Assuming you pass the chat_id as a URL parameter

        if chat and value not in chat.participants.all():
            raise ValidationError("The sender must be a participant in the chat.")

        return value

    def create(self, validated_data):
        """
        Create and return a new `Message` instance, given the validated data.
        """
        return Message.objects.create(**validated_data)
