from django.db.models import Count, Q
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import filters, generics, permissions

from apps.user.permissions_role import IsAdmin
from utils.response import BaseResponseMixin

from .models import FAQ
from .serializers import FAQCreateUpdateSerializer, FAQSerializer


class FAQListCreateView(BaseResponseMixin, generics.ListCreateAPIView):
    queryset = FAQ.objects.all()
    serializer_class = FAQSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = {
        "category": ["exact"],
        "is_published": ["exact"],
        "created_at": ["gte", "lte"],
        "updated_at": ["gte", "lte"],
    }
    search_fields = ["question", "answer", "category"]
    ordering_fields = ["created_at", "updated_at", "category", "question"]
    ordering = ["-created_at"]

    @swagger_auto_schema(
        operation_summary="FAQ 목록 조회",
        operation_description="FAQ(자주 묻는 질문) 목록을 조회합니다.",
        responses={
            200: openapi.Response("성공적으로 FAQ 목록을 반환합니다.", FAQSerializer(many=True)),
            400: "잘못된 요청입니다.",
            401: "인증이 필요합니다.",
            403: "접근 권한이 없습니다.",
        },
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="FAQ 등록",
        operation_description="새로운 FAQ를 등록합니다. (관리자만 가능)",
        responses={
            201: openapi.Response("FAQ가 성공적으로 등록되었습니다.", FAQSerializer),
            400: "잘못된 요청입니다.",
            401: "인증이 필요합니다.",
            403: "접근 권한이 없습니다.",
        },
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def get_queryset(self):
        # drf-yasg 스키마 생성용 분기
        if getattr(self, "swagger_fake_view", False):
            return FAQ.objects.none()
        queryset = FAQ.objects.only("id", "question", "answer", "category", "is_published", "created_at")

        # 관리자가 아니면 is_published=True인 FAQ만 조회
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_published=True)

        # 검색어가 있는 경우
        search_query = self.request.query_params.get("search", "")
        if search_query:
            queryset = queryset.filter(
                Q(question__icontains=search_query)
                | Q(answer__icontains=search_query)
                | Q(category__icontains=search_query),
            )

        return queryset

    def get_serializer_class(self):
        if self.request.method == "POST":
            return FAQCreateUpdateSerializer
        return FAQSerializer

    def perform_create(self, serializer):
        # 관리자만 FAQ를 생성할 수 있도록 권한 검사
        if not self.request.user.is_staff:
            self.permission_denied(self.request)
        serializer.save()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        data = serializer.data
        self.logger.info(f"FAQ created by {request.user.email if request.user.is_authenticated else 'anonymous'}")
        return self.success(data=data, message="FAQ가 생성되었습니다.", status=201)


class FAQDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = FAQ.objects.all()
    serializer_class = FAQSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    lookup_field = "pk"

    @swagger_auto_schema(
        operation_summary="FAQ 상세 조회",
        operation_description="특정 FAQ의 상세 정보를 조회합니다.",
        responses={
            200: openapi.Response("성공적으로 FAQ 상세 정보를 반환합니다.", FAQSerializer),
            400: "잘못된 요청입니다.",
            401: "인증이 필요합니다.",
            403: "접근 권한이 없습니다.",
            404: "FAQ를 찾을 수 없습니다.",
        },
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="FAQ 수정",
        operation_description="FAQ 정보를 수정합니다. (관리자만 가능)",
        responses={
            200: openapi.Response("FAQ가 성공적으로 수정되었습니다.", FAQSerializer),
            400: "잘못된 요청입니다.",
            401: "인증이 필요합니다.",
            403: "접근 권한이 없습니다.",
            404: "FAQ를 찾을 수 없습니다.",
        },
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="FAQ 부분 수정",
        operation_description="FAQ 정보를 부분 수정합니다. (관리자만 가능)",
        responses={
            200: openapi.Response("FAQ가 성공적으로 수정되었습니다.", FAQSerializer),
            400: "잘못된 요청입니다.",
            401: "인증이 필요합니다.",
            403: "접근 권한이 없습니다.",
            404: "FAQ를 찾을 수 없습니다.",
        },
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="FAQ 삭제",
        operation_description="FAQ를 삭제합니다. (관리자만 가능)",
        responses={
            204: "FAQ가 성공적으로 삭제되었습니다.",
            400: "잘못된 요청입니다.",
            401: "인증이 필요합니다.",
            403: "접근 권한이 없습니다.",
            404: "FAQ를 찾을 수 없습니다.",
        },
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return FAQ.objects.none()
        return super().get_queryset()


class PublishedFAQListView(generics.ListAPIView):
    queryset = FAQ.objects.filter(is_published=True)
    serializer_class = FAQSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = {
        "category": ["exact"],
        "created_at": ["gte", "lte"],
        "updated_at": ["gte", "lte"],
    }
    search_fields = ["question", "answer", "category"]
    ordering_fields = ["created_at", "updated_at", "category", "question"]
    ordering = ["-created_at"]

    @swagger_auto_schema(
        operation_summary="공개 FAQ 목록 조회",
        operation_description="공개된 FAQ(자주 묻는 질문) 목록을 조회합니다.",
        responses={
            200: openapi.Response("성공적으로 공개 FAQ 목록을 반환합니다.", FAQSerializer(many=True)),
            400: "잘못된 요청입니다.",
        },
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return FAQ.objects.none()
        queryset = super().get_queryset()

        # 검색어가 있는 경우
        search_query = self.request.query_params.get("search", "")
        if search_query:
            queryset = queryset.filter(
                Q(question__icontains=search_query)
                | Q(answer__icontains=search_query)
                | Q(category__icontains=search_query),
            )

        return queryset
