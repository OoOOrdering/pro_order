# from apps.idol.models import Idol, Member, Album, Schedule, Fanclub
# from apps.idol.serializers import IdolSerializer
# MemberSerializer, AlbumSerializer, ScheduleSerializer, \
#     FanclubSerializer
import django_filters
from rest_framework import serializers

from apps.idol.models import Idol


class IdolFilter(django_filters.FilterSet):
    """
    아이돌 검색 필터

    Attributes:
        name (str): 아이돌 이름 (부분 일치)
        agency (str): 소속사 (부분 일치)
        debut_date (date): 데뷔 날짜 (이후)
        debut_date_end (date): 데뷔 날짜 (이전)
    """

    name = django_filters.CharFilter(lookup_expr="icontains")
    agency = django_filters.CharFilter(lookup_expr="icontains")
    debut_date = django_filters.DateFilter(lookup_expr="gte")
    debut_date_end = django_filters.DateFilter(
        field_name="debut_date", lookup_expr="lte"
    )

    class Meta:
        model = Idol
        fields = ["name", "agency", "debut_date", "debut_date_end"]


class IdolSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    """아이돌 정보 시리얼라이저"""

    class Meta:
        model = Idol
        fields = [
            "id",
            "name",
            "en_name",
            "debut_date",
            "agency",
            "description",
            "profile_image",
            "is_active",
            "created_at",
            "updated_at",
            "image_url",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_image_url(self, obj):
        image = obj.images.first()
        if image and image.image_url:
            return image.image_url
        return None
