from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from base.models import Event, Task
from base.serializers import EventSerializer, TaskSerializer


class TaskViewSet(ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Task.objects.filter(owner=self.request.user, completed=False)


class EventViewSet(ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Event.objects.filter(owner=self.request.user)
