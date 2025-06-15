from django.db import models


class TimestampModel(models.Model):
    created_at = models.DateTimeField("생성일자", auto_now_add=True)
    updated_at = models.DateTimeField("수정일자", auto_now=True)

    class Meta:
        abstract = True


class CloudinaryImageMixin(models.Model):
    image_url = models.URLField("이미지 URL", blank=True, null=True)
    image_public_id = models.CharField(
        "Cloudinary public ID", max_length=255, blank=True, null=True
    )

    class Meta:
        abstract = True

    def get_thumbnail_url(self, width=300, height=300, crop="fill"):
        if self.image_url and "/upload/" in self.image_url:
            return self.image_url.replace(
                "/upload/", f"/upload/w_{width},h_{height},c_{crop}/"
            )
        return self.image_url
