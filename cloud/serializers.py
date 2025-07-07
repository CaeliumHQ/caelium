from rest_framework import serializers

from cloud.models import MediaFile


class MediaSerializer(serializers.ModelSerializer):
    """
    Serializer for media objects.
    """

    class Meta:
        model = MediaFile
        fields = ["location"]
