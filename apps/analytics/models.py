from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.user.models import User  # 사용자 모델 임포트


class DailyAnalytics(models.Model):
    date = models.DateField(unique=True, verbose_name="날짜")
    page_views = models.IntegerField(default=0, verbose_name="페이지 조회수")
    unique_visitors = models.IntegerField(default=0, verbose_name="고유 방문자 수")
    conversion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="전환율")
    average_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="평균 주문 금액")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일시")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일시")

    class Meta:
        verbose_name = "일별 분석"
        verbose_name_plural = "일별 분석"
        ordering = ["date"]

    def __str__(self):
        return f"일별 분석: {self.date}"


class EventLog(models.Model):
    class EventType(models.TextChoices):
        PAGE_VIEW = "PAGE_VIEW", _("페이지 조회")
        CLICK = "CLICK", _("클릭")
        FORM_SUBMISSION = "FORM_SUBMISSION", _("폼 제출")
        PURCHASE = "PURCHASE", _("구매")
        LOGIN = "LOGIN", _("로그인")
        LOGOUT = "LOGOUT", _("로그아웃")
        API_CALL = "API_CALL", _("API 호출")
        ERROR = "ERROR", _("에러")
        OTHER = "OTHER", _("기타")

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="event_logs",
        verbose_name="사용자",
    )
    event_name = models.CharField(max_length=255, verbose_name="이벤트 이름")
    event_type = models.CharField(
        _("이벤트 타입"),
        max_length=50,
        choices=EventType.choices,
        default=EventType.OTHER,
    )
    value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="값")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="타임스탬프")
    object_id = models.PositiveIntegerField(blank=True, null=True, verbose_name="관련 객체 ID")
    object_type = models.CharField(max_length=100, blank=True, null=True, verbose_name="관련 객체 타입")
    metadata = models.JSONField(blank=True, null=True, verbose_name="메타데이터")

    class Meta:
        verbose_name = "이벤트 로그"
        verbose_name_plural = "이벤트 로그"
        ordering = ["-timestamp"]

    def __str__(self):
        return f"[{self.event_type}] {self.event_name} by {self.user.email if self.user else 'Anonymous'} at {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
