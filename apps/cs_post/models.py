from django.db import models

from apps.user.models import User


class CSPost(models.Model):
    POST_TYPE_CHOICES = [
        ("inquiry", "문의"),
        ("report", "신고"),
        ("suggestion", "건의"),
        ("etc", "기타"),
    ]
    STATUS_CHOICES = [
        ("pending", "대기 중"),
        ("in_progress", "처리 중"),
        ("completed", "완료"),
        ("closed", "종료"),
    ]

    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="cs_posts", verbose_name="작성자")
    post_type = models.CharField(
        max_length=20,
        choices=POST_TYPE_CHOICES,
        default="inquiry",
        verbose_name="게시물 유형",
    )
    title = models.CharField(max_length=255, verbose_name="제목")
    content = models.TextField(verbose_name="내용")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending", verbose_name="상태")
    attachment = models.FileField(upload_to="cs_attachments/", blank=True, null=True, verbose_name="첨부파일")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일시")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일시")

    class Meta:
        verbose_name = "CS Post"
        verbose_name_plural = "CS Posts"
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.get_post_type_display()}] {self.title} ({self.get_status_display()})"
