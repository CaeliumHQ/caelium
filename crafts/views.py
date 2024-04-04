from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from crafts.models import Craft
from crafts.serializers import CraftSerializer


class CraftViewSet(ModelViewSet):
    queryset = Craft.objects.all()
    serializer_class = CraftSerializer
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        for craft in queryset:
            craft.content = " ".join(craft.content.split()[:60])
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
