import os

from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework import serializers

from accounts.models import User
from accounts.serializers import UserSerializer
from base.utils import log_admin

from .models import Chat, Message


class ChatSerializer(serializers.ModelSerializer):
    last_message = serializers.SerializerMethodField()
    participants = UserSerializer(many=True, read_only=True)
    participant_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Chat
        fields = (
            "id",
            "last_message",
            "updated_time",
            "is_group",
            "name",
            "participants",
            "group_icon",
            "participant_ids",
        )

    def get_last_message(self, obj):
        last_message = obj.message_set.last()
        if last_message:
            return LastMessageSerializer(last_message).data
        return None

    def create(self, validated_data):
        current_user = self.context["request"].user
        participant_ids = self.context["request"].data.get("participant_ids", [])
        
        if not participant_ids:
            raise serializers.ValidationError("At least one participant ID is required")
        
        # Convert single ID to list if necessary
        if isinstance(participant_ids, (int, str)):
            participant_ids = [int(participant_ids)]
            
        try:
            participant_users = [User.objects.get(pk=p_id) for p_id in participant_ids]
        except User.DoesNotExist as exc:
            raise serializers.ValidationError("One or more participants do not exist") from exc
            
        # Check for existing chat with these participants
        for participant in participant_users:
            existing_chats = Chat.objects.filter(participants=current_user).filter(participants=participant)
            if existing_chats.exists() and len(participant_ids) == 1:
                return existing_chats.first()
        
        # Create new chat
        chat = Chat.objects.create()
        chat.participants.add(current_user)
        for participant in participant_users:
            chat.participants.add(participant)
            
        return chat


class LastMessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer()

    class Meta:
        model = Message
        fields = ("content", "timestamp", "sender", "type")


class GroupChatSerializer(serializers.ModelSerializer):
    participants = serializers.PrimaryKeyRelatedField(many=True, queryset=User.objects.all())
    name = serializers.CharField(required=True)

    class Meta:
        model = Chat
        fields = ("id", "name", "participants", "updated_time")

    def validate_participants(self, value):
        if len(value) < 2:  # minimum 3 participants for group chat
            raise serializers.ValidationError("Group chat requires at least 3 participants")
        current_user = self.context["request"].user
        if current_user not in value:
            value.append(current_user)
        return value

    def create(self, validated_data):
        chat = Chat.objects.create(name=validated_data["name"], is_group=True)
        chat.participants.set(validated_data["participants"])
        return chat


class MessageSerializer(serializers.ModelSerializer):
    size = serializers.SerializerMethodField()
    extension = serializers.SerializerMethodField()
    file_name = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = "__all__"

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
