from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import filters, generics, permissions, serializers, status
from rest_framework.response import Response

from apps.cs_post.models import CSPost
from utils.response import BaseResponseMixin

from .models import CSReply
from .serializers import CSReplyCreateSerializer, CSReplySerializer, CSReplyUpdateSerializer


class CSReplyListCreateView(BaseResponseMixin, generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["author"]
    search_fields = ["content"]
    ordering_fields = ["created_at", "updated_at"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return CSReply.objects.none()
        post_pk = self.kwargs.get("cs_post_pk")
        try:
            cs_post = CSPost.objects.get(pk=post_pk)
        except CSPost.DoesNotExist:
            return CSReply.objects.none()
        queryset = CSReply.objects.select_related("author", "post").filter(post=cs_post)
        if not self.request.user.is_staff:
            queryset = queryset.filter(post__author=self.request.user)
        return queryset

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CSReplyCreateSerializer
        return CSReplySerializer

    def perform_create(self, serializer):
        # 관리자만 답변을 작성할 수 있도록 권한 검사
        if not self.request.user.is_staff:
            self.permission_denied(self.request, message="관리자만 답변을 작성할 수 있습니다.")

        post_pk = self.kwargs.get("cs_post_pk")
        try:
            cs_post = CSPost.objects.get(pk=post_pk)
        except CSPost.DoesNotExist:
            raise serializers.ValidationError({"detail": "문의글을 찾을 수 없습니다."})

        serializer.save(author=self.request.user, post=cs_post)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        # 생성 후 전체 정보 반환
        instance = serializer.instance
        response_serializer = CSReplySerializer(instance)
        data = response_serializer.data
        self.logger.info(f"CSReply created by {request.user.email if request.user.is_authenticated else 'anonymous'}")
        return self.success(data=data, message="CS 답변이 생성되었습니다.", status=201)

    @swagger_auto_schema(
        operation_summary="CS 답변 목록 조회",
        operation_description="특정 문의글에 대한 답변 목록을 조회합니다. (관리자는 전체, 일반 사용자는 본인 문의글에 대한 답변만 조회)",
        tags=["CSReply"],
        responses={
            200: openapi.Response("CS 답변 목록을 정상적으로 조회하였습니다."),
            401: "인증되지 않은 사용자입니다.",
            404: "문의글을 찾을 수 없습니다.",
        },
    )
    def get(self, request, *args, **kwargs):
        """CS 답변 목록 조회"""
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="CS 답변 작성",
        operation_description="특정 문의글에 대해 답변을 작성합니다. (관리자만 가능)",
        tags=["CSReply"],
        responses={
            201: openapi.Response("CS 답변이 정상적으로 작성되었습니다."),
            400: "요청 데이터가 올바르지 않습니다.",
            401: "인증되지 않은 사용자입니다.",
            403: "접근 권한이 없습니다.",
            404: "문의글을 찾을 수 없습니다.",
        },
    )
    def post(self, request, *args, **kwargs):
        """CS 답변 작성"""
        return super().post(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return Response(
                {
                    "message": "답변 목록을 조회했습니다.",
                    "data": {
                        "count": self.paginator.page.paginator.count,
                        "next": self.paginator.get_next_link(),
                        "previous": self.paginator.get_previous_link(),
                        "results": serializer.data,
                    },
                }
            )

        serializer = self.get_serializer(queryset, many=True)
        return Response({"message": "답변 목록을 조회했습니다.", "data": serializer.data})


class CSReplyDetailView(BaseResponseMixin, generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "pk"

    def check_admin_permission(self, request, action="access"):
        if not request.user.is_staff:
            self.permission_denied(request, message=f"관리자만 답변을 {action}할 수 있습니다.")

    def get_queryset(self):
        # 수정/삭제 작업 시 관리자 권한 검사
        if self.request.method in ["PUT", "PATCH", "DELETE"]:
            self.check_admin_permission(self.request, "수정" if self.request.method in ["PUT", "PATCH"] else "삭제")

        post_pk = self.kwargs.get("cs_post_pk")
        try:
            cs_post = CSPost.objects.get(pk=post_pk)
        except CSPost.DoesNotExist:
            raise serializers.ValidationError({"detail": "문의글을 찾을 수 없습니다."})
        queryset = CSReply.objects.select_related("author", "post").filter(post=cs_post)
        if not self.request.user.is_staff:
            queryset = queryset.filter(post__author=self.request.user)
        return queryset

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return CSReplyUpdateSerializer
        return CSReplySerializer

    def perform_update(self, serializer):
        if not self.request.user.is_staff:
            self.permission_denied(self.request, message="관리자만 답변을 수정할 수 있습니다.")
        super().perform_update(serializer)
        self.logger.info(
            f"CSReply updated by {self.request.user.email if self.request.user.is_authenticated else 'anonymous'}"
        )

    def perform_destroy(self, instance):
        if not self.request.user.is_staff:
            self.permission_denied(self.request, message="관리자만 답변을 삭제할 수 있습니다.")
        super().perform_destroy(instance)
        self.logger.info(
            f"CSReply deleted by {self.request.user.email if self.request.user.is_authenticated else 'anonymous'}"
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return self.success(data=serializer.data, message="답변 상세 정보를 조회했습니다.")

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        response_serializer = CSReplySerializer(instance)
        return self.success(data=response_serializer.data, message="답변이 수정되었습니다.")

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return self.success(data=None, message="답변이 삭제되었습니다.", status=status.HTTP_204_NO_CONTENT)
