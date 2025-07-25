import logging
import typing

from django.db.models import Count, Q
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import filters, generics, permissions
from rest_framework.response import Response

from utils.response import BaseResponseMixin

from .models import Notice
from .serializers import NoticeCreateUpdateSerializer, NoticeSerializer


class NoticeListCreateView(BaseResponseMixin, generics.ListCreateAPIView):
    logger = logging.getLogger("apps")
    """
    공지사항 목록을 조회하고 새로운 공지사항을 생성하는 뷰입니다.

    관리자는 공지사항을 생성할 수 있습니다.
    """

    queryset = Notice.objects.all()
    serializer_class = NoticeSerializer
    permission_classes: typing.ClassVar = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends: typing.ClassVar = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields: typing.ClassVar = {
        "is_published": ["exact"],
        "is_important": ["exact"],
        "author": ["exact"],
        "created_at": ["gte", "lte"],
        "updated_at": ["gte", "lte"],
    }
    search_fields: typing.ClassVar = ["title", "content"]
    ordering_fields: typing.ClassVar = [
        "created_at",
        "updated_at",
        "view_count",
        "is_important",
    ]
    ordering: typing.ClassVar = ["-is_important", "-created_at"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Notice.objects.none()
        queryset = Notice.objects.only(
            "id",
            "title",
            "content",
            "author",
            "is_published",
            "created_at",
        )
        search_query = self.request.query_params.get("search", "")
        if search_query:
            queryset = queryset.filter(Q(title__icontains=search_query) | Q(content__icontains=search_query))
        return queryset

    def get_serializer_class(self):
        """
        HTTP 요청 메서드에 따라 적절한 시리얼라이저 클래스를 반환합니다.

        POST 요청의 경우 `NoticeCreateUpdateSerializer`를 사용하고, 그 외에는 `NoticeSerializer`를 사용합니다.
        """
        if self.request.method == "POST":
            return NoticeCreateUpdateSerializer
        return NoticeSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        # 생성된 객체를 NoticeSerializer로 재직렬화
        instance = serializer.instance
        response_serializer = NoticeSerializer(instance, context=self.get_serializer_context())
        data = response_serializer.data
        self.logger.info(f"Notice created by {request.user.email if request.user.is_authenticated else 'anonymous'}")
        return self.success(data=data, message="공지사항이 생성되었습니다.", status=201)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            # pagination response는 dict로 감싸서 self.success로 반환
            return self.success(data={"results": serializer.data}, message="공지사항 목록 조회 성공")
        serializer = self.get_serializer(queryset, many=True)
        return self.success(data={"results": serializer.data}, message="공지사항 목록 조회 성공")

    @swagger_auto_schema(
        operation_summary="공지사항 목록 조회",
        operation_description="공지사항 목록을 조회합니다.",
        tags=["Notice"],
        responses={
            200: openapi.Response("공지사항 목록을 정상적으로 조회하였습니다."),
            401: "인증되지 않은 사용자입니다.",
        },
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="공지사항 생성",
        operation_description="새로운 공지사항을 생성합니다. (관리자만 가능)",
        tags=["Notice"],
        responses={
            201: openapi.Response("공지사항이 정상적으로 생성되었습니다."),
            400: "요청 데이터가 올바르지 않습니다.",
            401: "인증되지 않은 사용자입니다.",
            403: "접근 권한이 없습니다.",
        },
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class NoticeDetailView(BaseResponseMixin, generics.RetrieveUpdateDestroyAPIView):
    """
    특정 공지사항의 상세 정보를 조회, 수정, 삭제하는 뷰입니다.

    공지사항 조회 시 조회수가 증가합니다.
    """

    queryset = Notice.objects.all()
    serializer_class = NoticeSerializer
    permission_classes: typing.ClassVar = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = "pk"

    def get_serializer_class(self):
        """
        HTTP 요청 메서드에 따라 적절한 시리얼라이저 클래스를 반환합니다.

        PUT 또는 PATCH 요청의 경우 `NoticeCreateUpdateSerializer`를 사용하고, 그 외에는 `NoticeSerializer`를 사용합니다.
        """
        if self.request.method in ["PUT", "PATCH"]:
            return NoticeCreateUpdateSerializer
        return NoticeSerializer

    def perform_update(self, serializer):
        """
        공지사항을 업데이트할 때, 요청을 보낸 사용자가 해당 공지사항의 작성자인지 확인합니다.

        작성자가 아닌 경우 권한 거부 오류를 발생시킵니다.
        """
        if serializer.instance.author != self.request.user:
            self.permission_denied(self.request)
        super().perform_update(serializer)

    def perform_destroy(self, instance):
        """
        공지사항을 삭제할 때, 요청을 보낸 사용자가 해당 공지사항의 작성자인지 확인합니다.

        작성자가 아닌 경우 권한 거부 오류를 발생시킵니다.
        """
        if instance.author != self.request.user:
            self.permission_denied(self.request)
        super().perform_destroy(instance)

    def retrieve(self, request, *args, **kwargs):  # noqa: ARG002
        """특정 공지사항을 조회하고, 조회수를 1 증가시킵니다."""
        instance = self.get_object()
        instance.view_count += 1
        instance.save()
        serializer = self.get_serializer(instance)
        return self.success(data=serializer.data, message="공지사항 상세 조회 성공")

    @swagger_auto_schema(
        operation_summary="공지사항 상세 조회",
        operation_description="특정 공지사항의 상세 정보를 조회합니다.",
        tags=["Notice"],
        responses={
            200: openapi.Response("공지사항 정보를 정상적으로 조회하였습니다."),
            401: "인증되지 않은 사용자입니다.",
            403: "접근 권한이 없습니다.",
            404: "공지사항을 찾을 수 없습니다.",
        },
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="공지사항 수정",
        operation_description="공지사항 정보를 수정합니다. (작성자만 가능)",
        tags=["Notice"],
        responses={
            200: openapi.Response("공지사항 정보가 정상적으로 수정되었습니다."),
            400: "요청 데이터가 올바르지 않습니다.",
            401: "인증되지 않은 사용자입니다.",
            403: "접근 권한이 없습니다.",
            404: "공지사항을 찾을 수 없습니다.",
        },
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="공지사항 부분 수정",
        operation_description="공지사항 정보를 부분 수정합니다. (작성자만 가능)",
        tags=["Notice"],
        responses={
            200: openapi.Response("공지사항 정보가 정상적으로 수정되었습니다."),
            400: "요청 데이터가 올바르지 않습니다.",
            401: "인증되지 않은 사용자입니다.",
            403: "접근 권한이 없습니다.",
            404: "공지사항을 찾을 수 없습니다.",
        },
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="공지사항 삭제",
        operation_description="공지사항을 삭제합니다. (작성자만 가능)",
        tags=["Notice"],
        responses={
            204: openapi.Response("공지사항이 정상적으로 삭제되었습니다."),
            401: "인증되지 않은 사용자입니다.",
            403: "접근 권한이 없습니다.",
            404: "공지사항을 찾을 수 없습니다.",
        },
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


class RecentNoticeListView(BaseResponseMixin, generics.ListAPIView):
    logger = logging.getLogger("apps")
    """
    최근 공지사항 목록을 조회하는 뷰입니다.

    게시된(is_published=True) 공지사항 중 중요한 공지사항 우선으로 최신 5개를 반환합니다.
    """

    serializer_class = NoticeSerializer
    permission_classes: typing.ClassVar = [permissions.AllowAny]
    pagination_class = None

    def get_queryset(self):
        """게시된 공지사항 중 중요도와 생성일자를 기준으로 정렬된 최신 5개의 공지사항을 반환합니다."""
        return Notice.objects.filter(is_published=True).order_by("-created_at")[:5]

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return self.success(data={"results": serializer.data}, message="최근 공지사항 목록 조회 성공")

    @swagger_auto_schema(
        operation_summary="최근 공지사항 목록 조회",
        operation_description="최근 게시된 공지사항 중 상위 5개를 조회합니다.",
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
