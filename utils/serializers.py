from rest_framework import serializers


class BaseSerializer(serializers.ModelSerializer):
    """
    공통 필드 및 메서드를 위한 BaseSerializer
    예시: created_at, updated_at, validate 등
    """

    created_at = serializers.DateTimeField(read_only=True, required=False)
    updated_at = serializers.DateTimeField(read_only=True, required=False)

    class Meta:
        abstract = True

    # 공통 유효성 검사 예시
    def validate(self, attrs):
        # ...필요시 공통 유효성 검사 추가...
        return super().validate(attrs)
