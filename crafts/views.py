from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from crafts.models import Craft
from crafts.serializers import CraftSerializer


class CraftViewSet(ModelViewSet):
    queryset = Craft.objects.all()
    serializer_class = CraftSerializer
    permission_classes = [IsAuthenticated]
