from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, permissions

from .models import Work
from .serializers import WorkCreateUpdateSerializer, WorkSerializer


class WorkListCreateView(generics.ListCreateAPIView):
    serializer_class = WorkSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = [
        "status",
        "work_type",
        "assignee",
        "order__order_number",
        "due_date",
    ]
    search_fields = ["title", "description", "order__order_number"]
    ordering_fields = ["created_at", "due_date", "status"]

    def get_queryset(self):
        # 관리자는 모든 작업 조회, 일반 사용자는 본인에게 할당된 작업만 조회
        if self.request.user.is_staff:
            return Work.objects.all()
        return Work.objects.filter(assignee=self.request.user)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return WorkCreateUpdateSerializer
        return WorkSerializer

    def perform_create(self, serializer):
        # 관리자만 작업 생성 가능
        if not self.request.user.is_staff:
            self.permission_denied(self.request)

        # 담당자가 지정되지 않은 경우, 현재 요청한 관리자를 담당자로 설정
        if serializer.validated_data.get("assignee") is None:
            serializer.validated_data["assignee"] = self.request.user

        serializer.save()


class WorkDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Work.objects.all()
    serializer_class = WorkSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "pk"

    def get_queryset(self):
        # 관리자는 모든 작업 조회/수정/삭제, 일반 사용자는 본인에게 할당된 작업만 조회/수정/삭제
        if self.request.user.is_staff:
            return Work.objects.all()
        return Work.objects.filter(assignee=self.request.user)

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return WorkCreateUpdateSerializer
        return WorkSerializer

    def perform_update(self, serializer):
        # 관리자만 수정 가능 (할당된 사용자도 수정 가능하게 할 경우 로직 변경 필요)
        if not self.request.user.is_staff and serializer.instance.assignee != self.request.user:
            self.permission_denied(self.request)

        # 상태가 COMPLETED로 변경되면 completed_at 설정
        if "status" in serializer.validated_data and serializer.validated_data["status"] == Work.WorkStatus.COMPLETED:
            serializer.validated_data["completed_at"] = timezone.now()
        elif "status" in serializer.validated_data and serializer.validated_data["status"] != Work.WorkStatus.COMPLETED:
            serializer.validated_data["completed_at"] = None

        serializer.save()

    def perform_destroy(self, instance):
        # 관리자만 삭제 가능 (할당된 사용자도 삭제 가능하게 할 경우 로직 변경 필요)
        if not self.request.user.is_staff and instance.assignee != self.request.user:
            self.permission_denied(self.request)
        super().perform_destroy(instance)
