# serializers.py
from rest_framework.serializers import ModelSerializer

from .models import Chat


class ChatSerializer(ModelSerializer):
    class Meta:
        model = Chat
        fields = ['id', 'name', 'participants']
