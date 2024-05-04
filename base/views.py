from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from base.models import Task
from base.serializers import TaskSerializer


class TaskViewSet(ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Task.objects.filter(owner=self.request.user)