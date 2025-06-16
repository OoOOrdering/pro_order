from rest_framework import serializers

from apps.user.serializers import UserSerializer

from .models import CSPost


class CSPostSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    post_type_display = serializers.CharField(source="get_post_type_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = CSPost
        fields = (
            "id",
            "author",
            "post_type",
            "post_type_display",
            "title",
            "content",
            "status",
            "status_display",
            "attachment",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("author", "created_at", "updated_at", "status")


class CSPostCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CSPost
        fields = ("post_type", "title", "content", "attachment")


class CSPostUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CSPost
        fields = ("title", "content", "attachment", "status")
