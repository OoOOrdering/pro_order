from django.db import models

from apps.user.models import User


class PresetMessage(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="preset_messages",
        null=True,
        blank=True,
    )  # 특정 사용자에게만 제공되는 메시지 (null=True, blank=True는 전역 메시지)
    title = models.CharField(max_length=255, verbose_name="제목")
    content = models.TextField(verbose_name="메시지 내용")
    is_active = models.BooleanField(default=True, verbose_name="활성 여부")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일시")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일시")

    class Meta:
        verbose_name = "사전 설정 메시지"
        verbose_name_plural = "사전 설정 메시지"
        ordering = ["title"]

    def __str__(self):
        return self.title
