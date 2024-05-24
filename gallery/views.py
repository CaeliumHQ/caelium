from rest_framework import viewsets
from .models import MediaFile
from .serializers import MediaFileSerializer
from rest_framework.permissions import IsAuthenticated


class MediaFileViewSet(viewsets.ModelViewSet):
    serializer_class = MediaFileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return MediaFile.objects.filter(owner=self.request.user)
