from django.db import models
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, permissions

from .models import PresetMessage
from .serializers import PresetMessageCreateUpdateSerializer, PresetMessageSerializer


class PresetMessageListCreateView(generics.ListCreateAPIView):
    serializer_class = PresetMessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = {
        "is_active": ["exact"],
        "user": ["exact"],
        "created_at": ["gte", "lte"],
        "updated_at": ["gte", "lte"],
    }
    search_fields = ["title", "content", "user__username"]
    ordering_fields = ["title", "created_at", "updated_at"]
    ordering = ["title"]

    def get_queryset(self):
        queryset = PresetMessage.objects.filter(models.Q(user=self.request.user) | models.Q(user__isnull=True))

        # 검색어가 있는 경우
        search_query = self.request.query_params.get("search", "")
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query)
                | Q(content__icontains=search_query)
                | Q(user__username__icontains=search_query),
            )

        return queryset

    def get_serializer_class(self):
        if self.request.method == "POST":
            return PresetMessageCreateUpdateSerializer
        return PresetMessageSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class PresetMessageDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PresetMessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "pk"

    def get_queryset(self):
        return PresetMessage.objects.filter(models.Q(user=self.request.user) | models.Q(user__isnull=True))

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return PresetMessageCreateUpdateSerializer
        return PresetMessageSerializer

    def perform_update(self, serializer):
        if serializer.instance.user != self.request.user and serializer.instance.user is not None:
            self.permission_denied(self.request)
        super().perform_update(serializer)

    def perform_destroy(self, instance):
        if instance.user != self.request.user and instance.user is not None:
            self.permission_denied(self.request)
        super().perform_destroy(instance)
