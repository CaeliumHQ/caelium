from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework import status

from crafts.models import Craft
from crafts.serializers import CraftSerializer


class CraftViewSet(ModelViewSet):
    queryset = Craft.objects.all()
    serializer_class = CraftSerializer
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        for craft in serializer.data:
            craft["content"] = " ".join(craft["content"].split()[:60])
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        craft = self.get_object()
        if craft.owner != request.user:
            return Response(
                {"detail": "You do not have permission to delete this craft."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().destroy(request, *args, **kwargs)
