from rest_framework import serializers

from base.models import Event, Task


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ["name", "completed", "id"]

    def create(self, validated_data):
        validated_data["owner"] = self.context["request"].user
        return super().create(validated_data)


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = "__all__"

    def create(self, validated_data):
        validated_data["owner"] = self.context["request"].user
        return super().create(validated_data)
