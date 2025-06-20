from django.conf import settings
from rest_framework import serializers

from apps.user.serializers import UserSerializer
from utils.profanity_filter import ProfanityFilter

from .models import CSPost

profanity_filter = ProfanityFilter()


class CSPostSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    post_type_display = serializers.CharField(source="get_post_type_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    attachment_url = serializers.SerializerMethodField()

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
            "attachment_url",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("author", "created_at", "updated_at", "status")

    def get_attachment_url(self, obj):
        if obj.attachment and hasattr(obj.attachment, "url"):
            return f"{settings.MEDIA_URL}{obj.attachment.name}"
        return None

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # POST_TYPE_CHOICES와 STATUS_CHOICES 정보 추가
        if self.context.get("request") and self.context["request"].method == "GET":
            representation["type_choices"] = [
                {"value": choice[0], "display": choice[1]} for choice in CSPost.POST_TYPE_CHOICES
            ]
            representation["status_choices"] = [
                {"value": choice[0], "display": choice[1]} for choice in CSPost.STATUS_CHOICES
            ]
        return representation


class CSPostCreateSerializer(serializers.ModelSerializer):
    attachment_url = serializers.URLField(required=False, write_only=True)

    class Meta:
        model = CSPost
        fields = ("post_type", "title", "content", "attachment", "attachment_url")

    def validate(self, attrs):
        attachment_url = attrs.pop("attachment_url", None)
        # TODO: 필요한 경우 attachment_url을 처리하여 attachment 필드에 저장
        if profanity_filter.contains_profanity(attrs.get("title", "")):
            raise serializers.ValidationError({"title": "제목에 부적절한 단어가 포함되어 있습니다."})
        if profanity_filter.contains_profanity(attrs.get("content", "")):
            raise serializers.ValidationError({"content": "내용에 부적절한 단어가 포함되어 있습니다."})
        return attrs


class CSPostUpdateSerializer(serializers.ModelSerializer):
    attachment_url = serializers.URLField(required=False, write_only=True)

    class Meta:
        model = CSPost
        fields = ("title", "content", "attachment", "attachment_url", "status")

    def validate(self, attrs):
        attachment_url = attrs.pop("attachment_url", None)
        # TODO: 필요한 경우 attachment_url을 처리하여 attachment 필드에 저장
        return attrs
