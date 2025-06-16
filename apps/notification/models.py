import typing

from django.db import models


class Notification(models.Model):
    """사용자에게 전달되는 알림을 관리하는 모델입니다.

    제목, 내용, 읽음 여부 등의 정보를 포함합니다.
    """

    user = models.ForeignKey(
        "user.User",
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name="사용자",
    )
    title = models.CharField(max_length=255, verbose_name="제목")
    content = models.TextField(verbose_name="내용")
    is_read = models.BooleanField(default=False, verbose_name="읽음 여부")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일시")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일시")

    class Meta:
        """알림 모델의 메타데이터를 정의합니다.

        모델의 표시 이름과 정렬 순서를 설정합니다.
        """

        verbose_name = "알림"
        verbose_name_plural = "알림"
        ordering: typing.ClassVar = ["-created_at"]

    def __str__(self):
        """알림의 문자열 표현을 반환합니다."""
        return self.title
