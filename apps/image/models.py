import logging

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from .image_utils import delete_from_cloudinary, generate_thumbnail_url

logger = logging.getLogger(__name__)


class Image(models.Model):
    image_url = models.URLField()
    public_id = models.CharField(max_length=255, blank=True, null=True)

    # GenericForeignKey 구성 요소
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)  # 연결된 모델의 종류 (User, Post 등)
    object_id = models.PositiveIntegerField()  # 연결된 모델 인스턴스의 PK
    content_object = GenericForeignKey("content_type", "object_id")  # 위 둘을 합쳐 실제 객체처럼 동작하게 함

    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.public_id or 'Uploaded Image'}"

    class Meta:
        db_table = "image"
        verbose_name = "이미지"
        verbose_name_plural = "이미지 목록"
        ordering = ["-uploaded_at"]

    def get_thumbnail_url(self, width=300, height=300, crop="fill"):
        """
        이미지의 썸네일 URL을 반환합니다.

        Args:
        ----
            width (int): 썸네일 너비
            height (int): 썸네일 높이
            crop (str): 자르기 방식

        Returns:
        -------
            str: 썸네일 URL

        """
        return generate_thumbnail_url(self.image_url, width, height, crop)

    def delete(self, *args, **kwargs):
        """이미지 삭제 시 Cloudinary에서도 삭제합니다."""
        if self.public_id:
            try:
                delete_from_cloudinary(self.public_id)
            except Exception as e:
                # Cloudinary 삭제 실패 시 로그 기록
                logger.warning(f"Failed to delete image from Cloudinary: {self.public_id}. Error: {e!s}")

        super().delete(*args, **kwargs)
