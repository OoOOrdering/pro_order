import typing

from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, permissions
from rest_framework.response import Response

from .models import Notice
from .serializers import NoticeCreateUpdateSerializer, NoticeSerializer


class NoticeListCreateView(generics.ListCreateAPIView):
    """공지사항 목록을 조회하고 새로운 공지사항을 생성하는 뷰입니다.

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
    search_fields: typing.ClassVar = ["title", "content", "author__username"]
    ordering_fields: typing.ClassVar = [
        "created_at",
        "updated_at",
        "view_count",
        "is_important",
    ]
    ordering: typing.ClassVar = ["-is_important", "-created_at"]

    def get_queryset(self):
        """요청 파라미터에 따라 필터링된 공지사항 쿼리셋을 반환합니다.

        'search' 쿼리 파라미터가 있을 경우 제목, 내용, 작성자 이름으로 검색합니다.
        """
        queryset = Notice.objects.all()

        # 검색어가 있는 경우
        search_query = self.request.query_params.get("search", "")
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query)
                | Q(content__icontains=search_query)
                | Q(author__username__icontains=search_query)
            )

        return queryset

    def get_serializer_class(self):
        """HTTP 요청 메서드에 따라 적절한 시리얼라이저 클래스를 반환합니다.

        POST 요청의 경우 `NoticeCreateUpdateSerializer`를 사용하고, 그 외에는 `NoticeSerializer`를 사용합니다.
        """
        if self.request.method == "POST":
            return NoticeCreateUpdateSerializer
        return NoticeSerializer

    def perform_create(self, serializer):
        """새로운 공지사항 객체를 생성할 때, 현재 요청을 보낸 사용자를 작성자로 설정합니다."""
        serializer.save(author=self.request.user)


class NoticeDetailView(generics.RetrieveUpdateDestroyAPIView):
    """특정 공지사항의 상세 정보를 조회, 수정, 삭제하는 뷰입니다.

    공지사항 조회 시 조회수가 증가합니다.
    """

    queryset = Notice.objects.all()
    serializer_class = NoticeSerializer
    permission_classes: typing.ClassVar = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = "pk"

    def get_serializer_class(self):
        """HTTP 요청 메서드에 따라 적절한 시리얼라이저 클래스를 반환합니다.

        PUT 또는 PATCH 요청의 경우 `NoticeCreateUpdateSerializer`를 사용하고, 그 외에는 `NoticeSerializer`를 사용합니다.
        """
        if self.request.method in ["PUT", "PATCH"]:
            return NoticeCreateUpdateSerializer
        return NoticeSerializer

    def perform_update(self, serializer):
        """공지사항을 업데이트할 때, 요청을 보낸 사용자가 해당 공지사항의 작성자인지 확인합니다.

        작성자가 아닌 경우 권한 거부 오류를 발생시킵니다.
        """
        if serializer.instance.author != self.request.user:
            self.permission_denied(self.request)
        super().perform_update(serializer)

    def perform_destroy(self, instance):
        """공지사항을 삭제할 때, 요청을 보낸 사용자가 해당 공지사항의 작성자인지 확인합니다.

        작성자가 아닌 경우 권한 거부 오류를 발생시킵니다.
        """
        if instance.author != self.request.user:
            self.permission_denied(self.request)
        super().perform_destroy(instance)

    def retrieve(self, request, *args, **kwargs):
        """특정 공지사항을 조회하고, 조회수를 1 증가시킵니다."""
        instance = self.get_object()
        instance.view_count += 1
        instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class RecentNoticeListView(generics.ListAPIView):
    """최근 공지사항 목록을 조회하는 뷰입니다.

    게시된(is_published=True) 공지사항 중 중요한 공지사항 우선으로 최신 5개를 반환합니다.
    """

    serializer_class = NoticeSerializer
    permission_classes: typing.ClassVar = [permissions.AllowAny]

    def get_queryset(self):
        """게시된 공지사항 중 중요도와 생성일자를 기준으로 정렬된 최신 5개의 공지사항을 반환합니다."""
        return Notice.objects.filter(is_published=True).order_by("-is_important", "-created_at")[:5]
