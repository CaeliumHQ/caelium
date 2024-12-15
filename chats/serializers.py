import os

from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework import serializers

from accounts.models import User
from accounts.serializers import UserSerializer
from base.utils import log_admin

from .models import Chat, Message


class ChatSerializer(serializers.ModelSerializer):
    other_participant = serializers.SerializerMethodField()
    last_message_content = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = (
            "id",
            "other_participant",
            "last_message_content",
            "updated_time",
        )

    def get_other_participant(self, obj):
        user = self.context["request"].user
        participants = obj.participants.exclude(id=user.id)
        if participants.exists():
            return UserSerializer(participants.first(), context=self.context).data
        return None

    def get_last_message_content(self, obj):
        last_message = obj.message_set.last()
        if last_message:
            if last_message.sender == self.context["request"].user:
                return f"You: {last_message.content}"
            return f"{last_message.sender.name}: {last_message.content}"
        return None

    def create(self, validated_data):
        current_user = self.context["request"].user
        participant_id = self.context["request"].data.get("participant")
        if not participant_id:
            raise serializers.ValidationError("Participant ID is required")
        try:
            participant = User.objects.get(pk=participant_id)
        except User.DoesNotExist as exc:
            raise serializers.ValidationError("Participant does not exist") from exc
        existing_chats = Chat.objects.filter(participants=current_user).filter(participants=participant_id)
        if existing_chats.exists():
            return existing_chats.first()
        chat = Chat.objects.create()
        chat.participants.add(current_user, participant)
        return chat


class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer()
    chat = ChatSerializer()
    side = serializers.SerializerMethodField()
    size = serializers.SerializerMethodField()
    extension = serializers.SerializerMethodField()
    file_name = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = "__all__"

    def get_side(self, obj):
        current_user = self.context["request"].user
        if obj.sender == current_user:
            return "right"
        return "left"

    def get_size(self, obj):
        if obj.file:
            size = obj.file.size
            if size < 1024 * 1024:
                return f"{size / 1024:.2f} KB"
            else:
                return f"{size / (1024 * 1024):.2f} MB"
        return None

    def get_extension(self, obj):
        if obj.file:
            return str(os.path.splitext(obj.file.name)[1]).replace(".", "").upper()
        return None

    def get_file_name(self, obj):
        if obj.file:
            return str(os.path.basename(obj.file.name))
        return None


class MessageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ["chat", "timestamp", "type", "content", "file", "id"]
        read_only_fields = ["sender", "chat", "type"]

    def create(self, validated_data):
        chat_id = self.context["view"].kwargs["chat_id"]
        validated_data["chat_id"] = chat_id
        validated_data["sender"] = self.context["request"].user
        uploaded_file = validated_data.get("file")
        chat = Chat.objects.get(id=chat_id)
        chat.updated_time = timezone.now()
        chat.save()
        if uploaded_file:
            file_extension = os.path.splitext(uploaded_file.name)[-1].lower()
            if file_extension in [".jpg", ".jpeg", ".png", ".gif"]:
                validated_data["type"] = "img"
            elif file_extension in [".mp3", ".wav", ".ogg", ".aac"]:
                validated_data["type"] = "aud"
            elif file_extension in [".mp4", ".avi", ".mov"]:
                validated_data["type"] = "vid"
            else:
                validated_data["type"] = "doc"
        else:
            validated_data["type"] = "txt"

        message = super().create(validated_data)
        log_admin(
            f"Message from {message.sender.name} to "
            f"{message.chat.participants.exclude(id=message.sender.id).first().name}: '{message.content}'"
        )

        return message

    def validate(self, data):
        content = data.get("content")
        file = data.get("file")

        if (content is None or content.strip() == "") and not file:
            raise ValidationError("Either content or file must be provided and content cannot be an empty string.")

        return data

    def validate_file(self, value):
        if value:
            max_size = 10 * 1024 * 1024  # 10 MB
            if value.size > max_size:
                raise serializers.ValidationError("File size cannot exceed 10 MB.")
            return value
