from django_filters import rest_framework as filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions
from rest_framework.filters import OrderingFilter

from utils.response import BaseResponseMixin

from .models import Like
from .serializers import LikeCreateSerializer, LikeSerializer


class LikeFilter(filters.FilterSet):
    created_at__gte = filters.DateTimeFilter(field_name="created_at", lookup_expr="date__gte")
    created_at__lte = filters.DateTimeFilter(field_name="created_at", lookup_expr="date__lte")

    class Meta:
        model = Like
        fields = {
            "content_type": ["exact"],
            "object_id": ["exact"],
        }


class LikeListCreateView(BaseResponseMixin, generics.ListCreateAPIView):
    serializer_class = LikeSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = LikeFilter
    ordering_fields = ["created_at"]

    def get_queryset(self):
        return Like.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return LikeCreateSerializer
        return LikeSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        data = serializer.data
        self.logger.info(f"Like created by {request.user.email if request.user.is_authenticated else 'anonymous'}")
        return self.success(data=data, message="좋아요가 생성되었습니다.", status=201)


class LikeDestroyView(BaseResponseMixin, generics.DestroyAPIView):
    queryset = Like.objects.all()
    serializer_class = LikeSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "pk"

    def perform_destroy(self, instance):
        if instance.user != self.request.user:
            self.permission_denied(self.request)
        instance.delete()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        self.logger.info(f"Like deleted by {request.user.email if request.user.is_authenticated else 'anonymous'}")
        return self.success(data=None, message="좋아요가 삭제되었습니다.", status=204)
