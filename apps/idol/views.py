from django_filters import rest_framework as dj_filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.idol.docs import (
    idol_create_docs,
    idol_delete_docs,
    idol_list_docs,
    idol_retrieve_docs,
    idol_search_docs,
    idol_update_docs,
)
from apps.idol.models import Idol
from apps.idol.serializers import IdolSerializer


class IdolFilter(dj_filters.FilterSet):
    name = dj_filters.CharFilter(lookup_expr="icontains")
    agency = dj_filters.CharFilter(lookup_expr="icontains")
    debut_date = dj_filters.DateFilter(lookup_expr="gte")
    debut_date_end = dj_filters.DateFilter(field_name="debut_date", lookup_expr="lte")

    class Meta:
        model = Idol
        fields = ["name", "agency", "debut_date", "debut_date_end"]


class IdolViewSet(ModelViewSet):
    queryset = Idol.objects.all()
    serializer_class = IdolSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = IdolFilter
    ordering_fields = ["debut_date", "name", "created_at"]
    ordering = ["name"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        if self.action in ["partial_update", "update", "destroy"]:
            return Idol.objects.all()
        return Idol.objects.filter(is_active=True)

    def perform_create(self, serializer):
        serializer.save(is_active=True)

    @idol_list_docs
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @idol_create_docs
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @idol_retrieve_docs
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @idol_update_docs
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @idol_update_docs
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @idol_delete_docs
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.deactivate()
        return Response(
            {"detail": "아이돌 정보가 비활성화되었습니다."}, status=status.HTTP_200_OK
        )

    @idol_search_docs
    @action(detail=False, methods=["get"])
    def search(self, request):
        name = request.query_params.get("name", "")
        idols = self.get_queryset().filter(name__icontains=name)
        serializer = self.get_serializer(idols, many=True)
        return Response(serializer.data)
