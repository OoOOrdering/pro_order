from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notification
from .serializers import NotificationSerializer


class NotificationListCreateView(generics.ListCreateAPIView):
    """
    알림 목록 조회 및 생성을 처리하는 뷰입니다.

    관리자는 모든 알림을 조회할 수 있으며, 일반 사용자는 본인에게 생성된 알림만 조회할 수 있습니다.
    알림 생성은 관리자만 가능합니다.
    """

    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["is_read", "created_at"]
    search_fields = ["title", "content"]
    ordering_fields = ["created_at", "is_read"]

    def get_queryset(self):
        # 관리자는 모든 알림 조회 가능, 일반 사용자는 본인에게 생성된 알림만 조회
        if self.request.user.is_staff:
            return Notification.objects.all()
        return Notification.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # 관리자만 알림 생성 가능 (user 필드 지정)
        if not self.request.user.is_staff:
            self.permission_denied(self.request)
        # 알림 생성 시 user 필드가 제공되지 않으면 에러 발생. 직접 user를 할당해야 함.
        # 만약 serializer에 user 필드가 writeable하다면 serializer.save(user=self.request.user) 대신 serializer.save()로 충분할 수 있음
        serializer.save()


class NotificationDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    개별 알림의 조회, 수정, 삭제를 처리하는 뷰입니다.

    관리자는 모든 알림을 조회/수정/삭제할 수 있으며, 일반 사용자는 본인에게 생성된 알림만 조회/수정/삭제할 수 있습니다.
    """

    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "pk"

    def get_queryset(self):
        # 관리자는 모든 알림 조회/수정/삭제 가능, 일반 사용자는 본인에게 생성된 알림만 조회/수정/삭제
        if self.request.user.is_staff:
            return Notification.objects.all()
        return Notification.objects.filter(user=self.request.user)

    def perform_update(self, serializer):
        # 알림 소유자 또는 관리자만 수정 가능
        if serializer.instance.user != self.request.user and not self.request.user.is_staff:
            self.permission_denied(self.request)
        super().perform_update(serializer)

    def perform_destroy(self, instance):
        # 알림 소유자 또는 관리자만 삭제 가능
        if instance.user != self.request.user and not self.request.user.is_staff:
            self.permission_denied(self.request)
        super().perform_destroy(instance)


class UnreadNotificationListView(generics.ListAPIView):
    """
    읽지 않은 알림 목록을 조회하는 뷰입니다.

    사용자별로 읽지 않은 알림을 생성일시 기준 내림차순으로 정렬하여 반환합니다.
    """

    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Notification.objects.filter(user=user, is_read=False).order_by("-created_at")


class MarkNotificationAsReadView(APIView):
    """
    알림을 읽음 상태로 표시하는 뷰입니다.

    특정 알림을 읽음 상태로 변경하며, 해당 알림이 존재하지 않거나 권한이 없는 경우 404 에러를 반환합니다.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            notification = Notification.objects.get(pk=pk, user=request.user)
            notification.is_read = True
            notification.save()
            return Response({"status": "marked as read"}, status=status.HTTP_200_OK)
        except Notification.DoesNotExist:
            return Response(
                {"error": "Notification not found or you do not have permission"},
                status=status.HTTP_404_NOT_FOUND,
            )


class NotificationUnreadCountView(APIView):
    """
    읽지 않은 알림의 개수를 조회하는 뷰입니다.

    사용자별로 읽지 않은 알림의 총 개수를 반환합니다.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):  # noqa: ARG002
        user = request.user
        unread_count = Notification.objects.filter(user=user, is_read=False).count()
        return Response({"unread_count": unread_count})
