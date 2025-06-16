from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from apps.user.models import User

# from apps.post.models import Post # 예시: 좋아요가 게시물에 적용될 수 있다고 가정


class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="likes", verbose_name="사용자")
    # Generic foreign key to allow liking different types of objects
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일시")

    class Meta:
        verbose_name = "Like"
        verbose_name_plural = "Likes"
        # 한 사용자가 한 객체에 두 번 좋아요를 누르지 못하도록 유니크 제약 조건 추가
        unique_together = ("user", "content_type", "object_id")
        ordering = ["-created_at"]

    def __str__(self):
        return f"Like by {self.user.username} on {self.content_object}"
