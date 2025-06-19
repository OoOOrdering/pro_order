from django.db.models import Count
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import filters, generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from utils.email import send_email_async
from utils.response import BaseResponseMixin

from .models import Notification
from .serializers import NotificationSerializer


class NotificationListCreateView(BaseResponseMixin, generics.ListCreateAPIView):
    """
    알림 목록 조회 및 생성을 처리하는 뷰입니다.

    관리자는 모든 알림을 조회할 수 있으며, 일반 사용자는 본인에게 생성된 알림만 조회할 수 있습니다.
    알림 생성은 관리자만 가능합니다.
    """

    queryset = Notification.objects.all()  # <--- queryset 속성 추가
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

    # 테스트에서 send_email_async를 mock하려면 'utils.email.send_email_async' 경로를 patch해야 함

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Notification.objects.none()
        qs = super().get_queryset().annotate(user_notification_count=Count("user"))
        # 관리자는 모든 알림 조회 가능, 일반 사용자는 본인에게 생성된 알림만 조회
        if self.request.user.is_staff:
            return qs
        return qs.filter(user=self.request.user)

    def perform_create(self, serializer):
        # 관리자만 알림 생성 가능 (user 필드 지정)
        if not self.request.user.is_staff:
            self.permission_denied(self.request)
        instance = serializer.save()
        # Celery 비동기 알림 이메일 발송 예시
        if instance.user and instance.user.email:
            send_email_async.delay(subject="새 알림 도착", message=instance.content, to_email=instance.user.email)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        # 생성된 객체를 NotificationSerializer로 재직렬화
        instance = serializer.instance
        response_serializer = NotificationSerializer(instance, context=self.get_serializer_context())
        data = response_serializer.data
        self.logger.info(
            f"Notification created by {request.user.email if request.user.is_authenticated else 'anonymous'}"
        )
        return self.success(data=data, message="알림이 생성되었습니다.", status=201)

    @swagger_auto_schema(
        operation_summary="알림 목록 조회",
        operation_description="알림 목록을 조회합니다. (관리자는 전체, 일반 사용자는 본인 알림만 조회)",
        tags=["Notification"],
        responses={
            200: openapi.Response("알림 목록을 정상적으로 조회했습니다.", NotificationSerializer(many=True)),
            401: "인증되지 않은 사용자입니다.",
        },
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="알림 생성",
        operation_description="새로운 알림을 생성합니다. (관리자만 가능)",
        tags=["Notification"],
        responses={
            201: openapi.Response("알림이 정상적으로 생성되었습니다.", NotificationSerializer),
            400: "요청 데이터가 올바르지 않습니다.",
            401: "인증되지 않은 사용자입니다.",
            403: "접근 권한이 없습니다.",
        },
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class NotificationDetailView(BaseResponseMixin, generics.RetrieveUpdateDestroyAPIView):
    """
    개별 알림의 조회, 수정, 삭제를 처리하는 뷰입니다.

    관리자: 모든 알림 조회/수정/삭제 가능, 일반 사용자: 본인 알림만 가능
    """

    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "pk"

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Notification.objects.none()
        # 관리자는 모든 알림 조회/수정/삭제 가능, 일반 사용자는 본인에게 생성된 알림만 조회/수정/삭제
        if self.request.user.is_staff:
            return Notification.objects.all()
        return Notification.objects.filter(user=self.request.user)

    def perform_update(self, serializer):
        # 알림 소유자 또는 관리자만 수정 가능
        if serializer.instance.user != self.request.user and not self.request.user.is_staff:
            self.permission_denied(self.request)
        super().perform_update(serializer)
        self.logger.info(
            f"Notification updated by {self.request.user.email if self.request.user.is_authenticated else 'anonymous'}"
        )

    def perform_destroy(self, instance):
        # 알림 소유자 또는 관리자만 삭제 가능
        if instance.user != self.request.user and not self.request.user.is_staff:
            self.permission_denied(self.request)
        super().perform_destroy(instance)
        self.logger.info(
            f"Notification deleted by {self.request.user.email if self.request.user.is_authenticated else 'anonymous'}"
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return self.success(data=serializer.data, message="알림 상세 정보를 조회했습니다.")

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        response_serializer = NotificationSerializer(instance)
        return self.success(data=response_serializer.data, message="알림이 수정되었습니다.")

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return self.success(data=None, message="알림이 삭제되었습니다.", status=204)

    @swagger_auto_schema(
        operation_summary="알림 상세 조회",
        operation_description="특정 알림의 상세 정보를 조회합니다.",
        tags=["Notification"],
        responses={
            200: openapi.Response("알림 정보를 정상적으로 조회했습니다.", NotificationSerializer),
            401: "인증되지 않은 사용자입니다.",
            403: "접근 권한이 없습니다.",
            404: "알림을 찾을 수 없습니다.",
        },
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="알림 수정",
        operation_description="알림 정보를 수정합니다. (알림 소유자 또는 관리자만 가능)",
        tags=["Notification"],
        responses={
            200: openapi.Response("알림 정보가 정상적으로 수정되었습니다.", NotificationSerializer),
            400: "요청 데이터가 올바르지 않습니다.",
            401: "인증되지 않은 사용자입니다.",
            403: "접근 권한이 없습니다.",
            404: "알림을 찾을 수 없습니다.",
        },
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="알림 삭제",
        operation_description="알림을 삭제합니다. (알림 소유자 또는 관리자만 가능)",
        tags=["Notification"],
        responses={
            204: openapi.Response("알림이 정상적으로 삭제되었습니다."),
            401: "인증되지 않은 사용자입니다.",
            403: "접근 권한이 없습니다.",
            404: "알림을 찾을 수 없습니다.",
        },
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


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

    @swagger_auto_schema(
        operation_summary="읽지 않은 알림 목록 조회",
        operation_description="사용자별로 읽지 않은 알림 목록을 조회합니다.",
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class MarkNotificationAsReadView(APIView):
    """
    알림을 읽음 상태로 표시하는 뷰입니다.

    특정 알림을 읽음 상태로 변경하며, 해당 알림이 존재하지 않거나 권한이 없는 경우 404 에러를 반환합니다.
    """

    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="알림 읽음 처리",
        operation_description="특정 알림을 읽음 상태로 표시합니다.",
    )
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

    @swagger_auto_schema(
        operation_summary="읽지 않은 알림 개수 조회",
        operation_description="사용자별로 읽지 않은 알림의 총 개수를 조회합니다.",
    )
    def get(self, request, *args, **kwargs):  # noqa: ARG002
        user = request.user
        unread_count = Notification.objects.filter(user=user, is_read=False).count()
        return Response({"unread_count": unread_count})


# 운영 자동화/모니터링 예시:
# - Sentry 연동: settings.py에 SENTRY_DSN 설정, sentry_sdk.init 호출
# - drf-yasg: /swagger/ 경로로 API 문서 자동화
# - Django Debug Toolbar: INSTALLED_APPS, MIDDLEWARE에 추가, 쿼리/템플릿/캐시 실시간 모니터링
# - 배포 자동화: scripts/deploy.sh 등으로 git pull, migrate, collectstatic, reload 자동화
# - DB 백업: scripts/backup.sh 등으로 주기적 백업 자동화
