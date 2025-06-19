import logging

from django.db.models import Count, Q
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import filters, generics, permissions, status
from rest_framework.exceptions import PermissionDenied, ValidationError

from utils.response import BaseResponseMixin

from .models import Review
from .serializers import ReviewCreateUpdateSerializer, ReviewSerializer


class ReviewListCreateView(BaseResponseMixin, generics.ListCreateAPIView):
    logger = logging.getLogger("apps")
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]  # 인증된 사용자만 생성, 누구나 조회
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = {
        "rating": ["exact", "gte", "lte"],
        "is_public": ["exact"],
        "is_best": ["exact"],
        "created_at": ["gte", "lte"],
    }
    search_fields = ["comment", "order__order_number", "reviewer__username"]
    ordering_fields = ["created_at", "rating", "is_best"]
    ordering = ["-created_at"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Review.objects.none()
        qs = Review.objects.select_related("order", "reviewer").only("id", "order", "reviewer", "rating", "created_at")
        order_id = self.request.query_params.get("order_id")
        reviewer_id = self.request.query_params.get("reviewer_id")

        if order_id:
            qs = qs.filter(order__id=order_id)
        if reviewer_id:
            qs = qs.filter(reviewer__id=reviewer_id)

        # 검색어가 있는 경우
        search_query = self.request.query_params.get("search", "")
        if search_query:
            qs = qs.filter(
                Q(comment__icontains=search_query)
                | Q(order__order_number__icontains=search_query)
                | Q(reviewer__username__icontains=search_query),
            )

        # qs = qs.annotate(order_count=Count('order'))  # 집계 예시
        return qs

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ReviewCreateUpdateSerializer
        return ReviewSerializer

    def perform_create(self, serializer):
        # 주문 상태 및 소유권 확인
        order = serializer.validated_data.get("order")
        if order:
            # 주문 소유자 확인
            if order.user != self.request.user:
                raise PermissionDenied("You can only review your own orders.")

            # 주문 상태 확인
            if order.status != "COMPLETED":
                raise ValidationError("You can only review completed orders.")

            # 중복 리뷰 확인
            if Review.objects.filter(order=order).exists():
                raise ValidationError("This order already has a review.")

        serializer.save(reviewer=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        # 생성된 인스턴스를 전체 필드로 직렬화
        response_serializer = self.get_serializer(serializer.instance)
        data = response_serializer.data
        self.logger.info(f"Review created by {request.user.email if request.user.is_authenticated else 'anonymous'}")
        return self.success(data=data, message="리뷰가 생성되었습니다.", status=201)

    @swagger_auto_schema(
        operation_summary="리뷰 목록 조회",
        operation_description="작성된 리뷰의 전체 목록을 조회합니다. 검색, 정렬, 필터링이 가능합니다.",
        tags=["Review"],
        responses={
            200: openapi.Response("리뷰 목록을 정상적으로 조회하였습니다."),
            401: "인증되지 않은 사용자입니다.",
        },
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="리뷰 생성",
        operation_description="주문이 완료된 건에 대해 리뷰를 작성합니다. 본인 주문만 작성할 수 있습니다.",
        tags=["Review"],
        responses={
            201: openapi.Response("리뷰가 정상적으로 생성되었습니다."),
            400: "요청 데이터가 올바르지 않습니다.",
            401: "인증되지 않은 사용자입니다.",
            403: "접근 권한이 없습니다.",
        },
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class ReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]  # 인증된 사용자만 수정/삭제
    lookup_field = "pk"

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return ReviewCreateUpdateSerializer
        return ReviewSerializer

    def perform_update(self, serializer):
        # 리뷰 작성자만 수정 가능하도록 제한
        if serializer.instance.reviewer != self.request.user:
            raise PermissionDenied("You can only update your own reviews.")
        serializer.save()

    def perform_destroy(self, instance):
        # 리뷰 작성자만 삭제 가능하도록 제한
        if instance.reviewer != self.request.user:
            raise PermissionDenied("You can only delete your own reviews.")
        instance.delete()

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Review.objects.none()
        return Review.objects.all()

    @swagger_auto_schema(
        operation_summary="리뷰 상세 조회",
        operation_description="특정 리뷰의 상세 정보를 조회합니다.",
        tags=["Review"],
        responses={
            200: openapi.Response("리뷰 정보를 정상적으로 조회하였습니다."),
            401: "인증되지 않은 사용자입니다.",
            403: "접근 권한이 없습니다.",
            404: "리뷰를 찾을 수 없습니다.",
        },
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="리뷰 수정",
        operation_description="특정 리뷰의 내용을 수정합니다. 작성자만 수정할 수 있습니다.",
        tags=["Review"],
        responses={
            200: openapi.Response("리뷰가 정상적으로 수정되었습니다."),
            400: "요청 데이터가 올바르지 않습니다.",
            401: "인증되지 않은 사용자입니다.",
            403: "접근 권한이 없습니다.",
            404: "리뷰를 찾을 수 없습니다.",
        },
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="리뷰 삭제",
        operation_description="특정 리뷰를 삭제합니다. 작성자만 삭제할 수 있습니다.",
        tags=["Review"],
        responses={
            204: openapi.Response("리뷰가 정상적으로 삭제되었습니다."),
            401: "인증되지 않은 사용자입니다.",
            403: "접근 권한이 없습니다.",
            404: "리뷰를 찾을 수 없습니다.",
        },
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


class UserReviewListView(generics.ListAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Review.objects.none()
        user_id = self.kwargs.get("user_id")
        return Review.objects.filter(reviewer_id=user_id)

    @swagger_auto_schema(
        operation_summary="사용자별 리뷰 목록 조회",
        operation_description="특정 사용자가 작성한 리뷰 목록을 조회합니다.",
        tags=["Review"],
        responses={
            200: openapi.Response("사용자별 리뷰 목록을 정상적으로 조회하였습니다."),
            401: "인증되지 않은 사용자입니다.",
            404: "사용자를 찾을 수 없습니다.",
        },
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
