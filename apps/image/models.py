from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class Image(models.Model):
    image_url = models.URLField()
    public_id = models.CharField(max_length=255, blank=True, null=True)

    # GenericForeignKey 구성 요소
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE
    )  # 연결된 모델의 종류 (User, Post 등)
    object_id = models.PositiveIntegerField()  # 연결된 모델 인스턴스의 PK
    content_object = GenericForeignKey(
        "content_type", "object_id"
    )  # 위 둘을 합쳐 실제 객체처럼 동작하게 함

    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.public_id or 'Uploaded Image'}"

    class Meta:
        db_table = "image"
        verbose_name = "이미지"
        verbose_name_plural = "이미지 목록"
        ordering = ["-uploaded_at"]

    def get_thumbnail_url(self, width=300, height=300, crop="fill"):
        # 썸네일 URL 동적 생성
        if not self.image_url:
            return ""
        return self.image_url.replace(
            "/upload/", f"/upload/w_{width},h_{height},c_{crop}/"
        )
