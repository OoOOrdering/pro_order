from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, permissions

from .models import Progress
from .serializers import ProgressCreateUpdateSerializer, ProgressSerializer


class ProgressListCreateView(generics.ListCreateAPIView):
    queryset = Progress.objects.all()
    serializer_class = ProgressSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = {
        "status": ["exact"],
        "current_step": ["exact"],
        "created_at": ["gte", "lte"],
        "updated_at": ["gte", "lte"],
        "estimated_completion_date": ["gte", "lte"],
        "actual_completion_date": ["gte", "lte"],
    }
    search_fields = ["order__order_number", "notes", "current_step"]
    ordering_fields = [
        "created_at",
        "updated_at",
        "status",
        "estimated_completion_date",
        "actual_completion_date",
    ]
    ordering = ["-created_at"]

    def get_queryset(self):
        queryset = Progress.objects.all()

        # 검색어가 있는 경우
        search_query = self.request.query_params.get("search", "")
        if search_query:
            queryset = queryset.filter(
                Q(order__order_number__icontains=search_query)
                | Q(notes__icontains=search_query)
                | Q(current_step__icontains=search_query)
            )

        return queryset

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ProgressCreateUpdateSerializer
        return ProgressSerializer

    def perform_create(self, serializer):
        serializer.save(last_updated_by=self.request.user)


class ProgressDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Progress.objects.all()
    serializer_class = ProgressSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "pk"

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return ProgressCreateUpdateSerializer
        return ProgressSerializer

    def perform_update(self, serializer):
        serializer.save(last_updated_by=self.request.user)
