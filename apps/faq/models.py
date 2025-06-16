from django.db import models


class FAQ(models.Model):
    question = models.TextField(verbose_name="질문")
    answer = models.TextField(verbose_name="답변")
    category = models.CharField(max_length=100, blank=True, null=True, verbose_name="카테고리")
    is_published = models.BooleanField(default=True, verbose_name="게시 여부")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일시")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일시")

    class Meta:
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"
        ordering = ["-created_at"]

    def __str__(self):
        return self.question
