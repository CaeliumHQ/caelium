from rest_framework import serializers

from crafts.models import Craft


class CraftSerializer(serializers.ModelSerializer):
    class Meta:
        model = Craft
        fields = ["title", "banner", "content", "date", "space"]

    def create(self, validated_data):
        validated_data["owner"] = self.context["request"].user
        return super().create(validated_data)
