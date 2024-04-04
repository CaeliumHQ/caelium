from rest_framework import serializers

from accounts.serializers import UserSerializer
from crafts.models import Craft


class CraftSerializer(serializers.ModelSerializer):
    time = serializers.SerializerMethodField()
    owner = UserSerializer()

    class Meta:
        model = Craft
        fields = '__all__'

    def create(self, validated_data):
        validated_data["owner"] = self.context["request"].user
        return super().create(validated_data)

    def get_time(self, instance):
        return f"{round(len(instance.content.split()) / 200, 2)} min"
