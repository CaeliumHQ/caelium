from rest_framework import serializers

from crafts.models import Craft


class CraftSerializer(serializers.ModelSerializer):
    time = serializers.SerializerMethodField()

    class Meta:
        model = Craft
        exclude = ["owner"]

    def create(self, validated_data):
        validated_data["owner"] = self.context["request"].user
        return super().create(validated_data)

    def get_time(self, instance):
        return f"{round(len(instance.content.split()) / 200, 2)} min"
