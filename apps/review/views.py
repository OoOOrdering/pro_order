from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, permissions
from rest_framework.exceptions import ValidationError

from .models import Review
from .serializers import ReviewCreateUpdateSerializer, ReviewSerializer


class ReviewListCreateView(generics.ListCreateAPIView):
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
        queryset = Review.objects.all()
        order_id = self.request.query_params.get("order_id")
        reviewer_id = self.request.query_params.get("reviewer_id")

        if order_id:
            queryset = queryset.filter(order__id=order_id)
        if reviewer_id:
            queryset = queryset.filter(reviewer__id=reviewer_id)

        # 검색어가 있는 경우
        search_query = self.request.query_params.get("search", "")
        if search_query:
            queryset = queryset.filter(
                Q(comment__icontains=search_query)
                | Q(order__order_number__icontains=search_query)
                | Q(reviewer__username__icontains=search_query),
            )

        return queryset

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ReviewCreateUpdateSerializer
        return ReviewSerializer

    def perform_create(self, serializer):
        # 이미 해당 주문에 대한 리뷰가 있는지 확인
        order = serializer.validated_data.get("order")
        if order and Review.objects.filter(order=order).exists():
            raise ValidationError("This order already has a review.")
        serializer.save(reviewer=self.request.user)


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
            self.permission_denied(self.request)
        super().perform_update(serializer)

    def perform_destroy(self, instance):
        # 리뷰 작성자만 삭제 가능하도록 제한
        if instance.reviewer != self.request.user:
            self.permission_denied(self.request)
        super().perform_destroy(instance)


class UserReviewListView(generics.ListAPIView):
    serializer_class = ReviewSerializer

    def get_queryset(self):
        user_id = self.kwargs.get("user_id")
        return Review.objects.filter(user_id=user_id)
