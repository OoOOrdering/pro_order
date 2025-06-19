from django.db import models

from apps.user.models import User


class DashboardSummary(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="dashboard_summary",
        verbose_name="사용자",
        null=True,
        blank=True,
    )  # 관리자용 전역 요약이거나, 사용자별 대시보드 요약
    total_orders = models.PositiveIntegerField(default=0, verbose_name="총 주문 수")
    pending_orders = models.PositiveIntegerField(default=0, verbose_name="대기 중인 주문 수")
    completed_orders = models.PositiveIntegerField(default=0, verbose_name="완료된 주문 수")
    total_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="총 수익")
    new_users_today = models.PositiveIntegerField(default=0, verbose_name="오늘 신규 사용자 수")
    active_chat_rooms = models.PositiveIntegerField(default=0, verbose_name="활성 채팅방 수")
    unresolved_cs_posts = models.PositiveIntegerField(default=0, verbose_name="미해결 CS 게시물 수")
    last_updated = models.DateTimeField(auto_now=True, verbose_name="마지막 업데이트")

    class Meta:
        verbose_name = "Dashboard Summary"
        verbose_name_plural = "Dashboard Summaries"

    def __str__(self):
        if self.user:
            return f"Dashboard Summary for {self.user.email}"
        return "Global Dashboard Summary"
