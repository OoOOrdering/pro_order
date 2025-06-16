from django.db import models

from apps.user.models import User


class Notice(models.Model):
    title = models.CharField(max_length=255, verbose_name="제목")
    content = models.TextField(verbose_name="내용")
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="작성자")
    is_published = models.BooleanField(default=True, verbose_name="게시 여부")
    is_important = models.BooleanField(default=False, verbose_name="중요 공지 여부")
    view_count = models.PositiveIntegerField(default=0, verbose_name="조회수")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일시")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일시")

    class Meta:
        verbose_name = "Notice"
        verbose_name_plural = "Notices"
        ordering = ["-is_important", "-created_at"]

    def __str__(self):
        return self.title
