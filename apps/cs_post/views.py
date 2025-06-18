from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, permissions

from .models import CSPost
from .serializers import CSPostCreateSerializer, CSPostSerializer, CSPostUpdateSerializer


class CSPostListCreateView(generics.ListCreateAPIView):
    serializer_class = CSPostSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["post_type", "status", "created_at"]
    search_fields = ["title", "content", "author__email"]
    ordering_fields = ["created_at", "updated_at", "status", "title"]

    def get_queryset(self):
        # 사용자는 본인이 작성한 게시물만 조회 가능, 관리자는 모든 게시물 조회
        if self.request.user.is_staff:
            return CSPost.objects.all()
        return CSPost.objects.filter(author=self.request.user)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CSPostCreateSerializer
        return CSPostSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class CSPostDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CSPostSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "pk"

    def get_queryset(self):
        # 사용자는 본인이 작성한 게시물만 조회/수정/삭제 가능, 관리자는 모든 게시물 조회/수정/삭제
        if self.request.user.is_staff:
            return CSPost.objects.all()
        return CSPost.objects.filter(author=self.request.user)

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return CSPostUpdateSerializer
        return CSPostSerializer

    def perform_update(self, serializer):
        # 작성자 또는 관리자만 수정 가능
        if serializer.instance.author != self.request.user and not self.request.user.is_staff:
            self.permission_denied(self.request)
        super().perform_update(serializer)

    def perform_destroy(self, instance):
        # 작성자 또는 관리자만 삭제 가능
        if instance.author != self.request.user and not self.request.user.is_staff:
            self.permission_denied(self.request)
        super().perform_destroy(instance)
