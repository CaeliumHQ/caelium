from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from base.models import Comment, Like, Post, Task
from base.serializers import CommentSerializer, LikeSerializer, PostCreateSerializer, PostSerializer, TaskSerializer


class TaskViewSet(ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Task.objects.filter(owner=self.request.user, completed=False)


class LikeViewSet(ModelViewSet):
    serializer_class = LikeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Like.objects.filter(user=self.request.user)


class CommentViewSet(ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Comment.objects.filter(owner=self.request.user)


class PostViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Post.objects.all()

    def get_serializer_class(self):
        if self.action  == 'create':
            return PostCreateSerializer
        return PostSerializer

    def create(self, request, *args, **kwargs):
        """
        Custom create method to handle post creation with different fields.
        Accepts: caption, media, tagged_users, allow_comments
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(owner=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
