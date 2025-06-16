from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.user.models import User


class Work(models.Model):
    class WorkType(models.TextChoices):
        DESIGN = "DESIGN", _("디자인")
        DEVELOPMENT = "DEVELOPMENT", _("개발")
        MARKETING = "MARKETING", _("마케팅")
        OTHER = "OTHER", _("기타")

    class WorkStatus(models.TextChoices):
        PENDING = "PENDING", _("대기 중")
        IN_PROGRESS = "IN_PROGRESS", _("진행 중")
        COMPLETED = "COMPLETED", _("완료")
        CANCELLED = "CANCELLED", _("취소됨")

    order = models.ForeignKey(
        "order.Order",
        on_delete=models.CASCADE,
        related_name="works",
        verbose_name="주문",
    )
    assignee = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_works",
        verbose_name="담당자",
    )
    work_type = models.CharField(_("작업 유형"), max_length=20, choices=WorkType.choices, default=WorkType.OTHER)
    title = models.CharField(max_length=255, verbose_name="제목")
    description = models.TextField(blank=True, verbose_name="설명")
    status = models.CharField(_("상태"), max_length=20, choices=WorkStatus.choices, default=WorkStatus.PENDING)
    due_date = models.DateTimeField(_("마감일"), null=True, blank=True)
    completed_at = models.DateTimeField(_("완료일"), null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일시")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일시")

    class Meta:
        verbose_name = "작업"
        verbose_name_plural = "작업"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
