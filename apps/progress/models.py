from django.db import models

from apps.order.models import Order


class Progress(models.Model):
    STATUS_CHOICES = [
        ("pending", "대기 중"),
        ("in_progress", "진행 중"),
        ("completed", "완료"),
        ("cancelled", "취소됨"),
        ("on_hold", "보류 중"),
    ]

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="progress", verbose_name="주문")
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default="pending",
        verbose_name="진행 상태",
    )
    current_step = models.CharField(max_length=255, blank=True, null=True, verbose_name="현재 단계")
    notes = models.TextField(blank=True, null=True, verbose_name="비고")
    estimated_completion_date = models.DateField(blank=True, null=True, verbose_name="예상 완료일")
    actual_completion_date = models.DateField(blank=True, null=True, verbose_name="실제 완료일")
    last_updated_by = models.ForeignKey(
        "user.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="마지막 업데이트 사용자",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일시")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일시")

    class Meta:
        verbose_name = "Progress"
        verbose_name_plural = "Progresses"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Progress for Order {self.order.order_number} - {self.status}"

    def save(self, *args, **kwargs):
        # 실제 완료일이 설정되면 상태를 'completed'로 변경
        if self.actual_completion_date and self.status != "completed":
            self.status = "completed"
        super().save(*args, **kwargs)
