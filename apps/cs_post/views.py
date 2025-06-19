from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, permissions, status
from rest_framework.response import Response

from utils.response import BaseResponseMixin

from .models import CSPost
from .serializers import CSPostCreateSerializer, CSPostSerializer, CSPostUpdateSerializer


class CSPostListCreateView(BaseResponseMixin, generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["post_type", "status"]
    search_fields = ["title", "content", "author__email"]
    ordering_fields = ["created_at", "updated_at", "status", "title"]

    def get_queryset(self):
        # 사용자는 본인이 작성한 게시물만 조회 가능, 관리자는 모든 게시물 조회
        if self.request.user.is_staff:
            return CSPost.objects.select_related("author").all()
        return CSPost.objects.select_related("author").filter(author=self.request.user)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CSPostCreateSerializer
        return CSPostSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        response_serializer = CSPostSerializer(serializer.instance)
        self.logger.info(f"CSPost created by {request.user.email if request.user.is_authenticated else 'anonymous'}")
        return self.success(data=response_serializer.data, message="문의가 등록되었습니다.", status=201)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.success(
                data={
                    "count": self.paginator.page.paginator.count,
                    "next": self.paginator.get_next_link(),
                    "previous": self.paginator.get_previous_link(),
                    "results": serializer.data,
                },
                message="문의 목록을 조회했습니다.",
            )

        serializer = self.get_serializer(queryset, many=True)
        return self.success(data=serializer.data, message="문의 목록을 조회했습니다.")


class CSPostDetailView(BaseResponseMixin, generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "pk"

    def get_queryset(self):
        # 사용자는 본인이 작성한 게시물만 조회/수정/삭제 가능, 관리자는 모든 게시물 조회/수정/삭제
        if self.request.user.is_staff:
            return CSPost.objects.select_related("author").all()
        return CSPost.objects.select_related("author").filter(author=self.request.user)

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return CSPostUpdateSerializer
        return CSPostSerializer

    def perform_update(self, serializer):
        # 작성자 또는 관리자만 수정 가능
        if serializer.instance.author != self.request.user and not self.request.user.is_staff:
            self.permission_denied(self.request, message="문의 작성자 또는 관리자만 수정할 수 있습니다.")
        super().perform_update(serializer)
        self.logger.info(
            f"CSPost updated by {self.request.user.email if self.request.user.is_authenticated else 'anonymous'}"
        )

    def perform_destroy(self, instance):
        # 작성자 또는 관리자만 삭제 가능
        if instance.author != self.request.user and not self.request.user.is_staff:
            self.permission_denied(self.request, message="문의 작성자 또는 관리자만 삭제할 수 있습니다.")
        super().perform_destroy(instance)
        self.logger.info(
            f"CSPost deleted by {self.request.user.email if self.request.user.is_authenticated else 'anonymous'}"
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return self.success(data=serializer.data, message="문의 상세 정보를 조회했습니다.")

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        response_serializer = CSPostSerializer(instance)
        return self.success(data=response_serializer.data, message="문의가 수정되었습니다.")

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return self.success(data=None, message="문의가 삭제되었습니다.", status=204)
