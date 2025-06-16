from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, permissions

from .models import Like
from .serializers import LikeCreateSerializer, LikeSerializer


class LikeListCreateView(generics.ListCreateAPIView):
    serializer_class = LikeSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["content_type", "object_id", "created_at"]
    ordering_fields = ["created_at"]

    def get_queryset(self):
        return Like.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return LikeCreateSerializer
        return LikeSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class LikeDestroyView(generics.DestroyAPIView):
    queryset = Like.objects.all()
    serializer_class = LikeSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "pk"

    def perform_destroy(self, instance):
        if instance.user != self.request.user:
            self.permission_denied(self.request)
        instance.delete()
