from django.db.models import Count, Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, permissions

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

    def get_queryset(self):
        # 예시: 필요한 필드만 조회
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
    permission_classes = [permissions.IsAdminUser]
    lookup_field = "pk"

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return FAQCreateUpdateSerializer
        return FAQSerializer


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

    def get_queryset(self):
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
