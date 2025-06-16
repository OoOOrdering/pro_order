from django.db import models

from apps.cs_post.models import CSPost
from apps.user.models import User


class CSReply(models.Model):
    post = models.ForeignKey(
        CSPost,
        on_delete=models.CASCADE,
        related_name="replies",
        verbose_name="고객지원 게시물",
    )
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="cs_replies", verbose_name="작성자")
    content = models.TextField(verbose_name="내용")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일시")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일시")

    class Meta:
        verbose_name = "CS Reply"
        verbose_name_plural = "CS Replies"
        ordering = ["created_at"]

    def __str__(self):
        return f'Reply to "{self.post.title}" by {self.author.username}'
