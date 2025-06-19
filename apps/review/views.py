import logging

from django.db.models import Count, Q
from django_filters.rest_framework import DjangoFilterBackend
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
        # 예시: 리뷰별 주문 정보, 작성자 정보 select_related, 리뷰 개수 집계, 필요한 필드만 조회
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


class UserReviewListView(generics.ListAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user_id = self.kwargs.get("user_id")
        return Review.objects.filter(reviewer_id=user_id)
