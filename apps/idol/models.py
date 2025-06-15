from django.contrib.contenttypes.fields import GenericRelation
from django.db import models

from apps.image.models import Image
from apps.user.models import User


class Idol(models.Model):
    """
    아이돌 정보를 저장하는 모델

    Attributes:
        name (str): 아이돌 이름
        debut_date (date, optional): 데뷔 날짜
        agency (str, optional): 소속사
        description (str): 소개글
        profile_image (str): 프로필 이미지 URL
        created_at (datetime): 생성 시간
        updated_at (datetime): 수정 시간
        is_active (bool): 활동 상태
    """

    name = models.CharField(max_length=100, db_index=True)  # 아이돌 이름
    en_name = models.CharField(max_length=255, blank=True)  # 아이돌 영문 이름
    debut_date = models.DateField(null=True, blank=True)  # 데뷔 날짜
    agency = models.CharField(max_length=100, null=True, blank=True)  # 소속사
    description = models.TextField(blank=True)  # 소개글
    profile_image = models.URLField(blank=True, null=True)  # 프로필 이미지 URL
    images = GenericRelation(Image, related_query_name="idol_image")
    created_at = models.DateTimeField(auto_now_add=True)  # 생성 시간
    updated_at = models.DateTimeField(auto_now=True)  # 수정 시간
    is_active = models.BooleanField(default=True)  # 활동 상태
    managers = models.ManyToManyField(User, related_name="managed_idols", blank=True)
    # 아이돌이랑 매니저 다대다 관계 설정

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["agency"]),
            models.Index(fields=["debut_date"]),
        ]
        verbose_name = "아이돌"
        verbose_name_plural = "아이돌들"

    def __str__(self):
        """아이돌의 문자열 표현을 반환합니다."""
        return self.name

    def deactivate(self):
        """아이돌을 비활성화합니다."""
        self.is_active = False
        self.save(update_fields=["is_active"])

    def activate(self):
        """아이돌을 활성화합니다."""
        self.is_active = True
        self.save(update_fields=["is_active"])
