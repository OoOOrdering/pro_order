from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from apps.image.models import Image
from apps.image.utils import delete_from_cloudinary, upload_to_cloudinary
from utils.exceptions import CustomAPIException
from utils.responses.image import (
    IMAGE_CANNOT_VALIDATE_OWNERSHIP,
    IMAGE_INVALID_MODEL,
    IMAGE_NO_PERMISSION,
    IMAGE_OBJECT_NOT_FOUND,
    IMAGE_REQUEST_MISSING,
)


class ImageUploadSerializer(serializers.ModelSerializer):
    object_type = serializers.CharField(write_only=True)
    object_id = serializers.IntegerField(write_only=True)
    image = serializers.ImageField(write_only=True, required=False)
    image_url = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Image
        fields = [
            "image_url",
            "public_id",
            "uploaded_at",
            "object_type",
            "object_id",
            "image",
        ]
        read_only_fields = ["public_id", "uploaded_at"]

    def validate(self, data):

        request = self.context.get("request")
        if not request:
            raise CustomAPIException(IMAGE_REQUEST_MISSING)

        try:
            content_type = ContentType.objects.get(model=data["object_type"].lower())
        except ContentType.DoesNotExist:
            raise CustomAPIException(IMAGE_INVALID_MODEL)

        # content_type의 모델 클래스을 반환
        model_class = content_type.model_class()

        try:
            target_instance = model_class.objects.get(pk=data["object_id"])
        except model_class.DoesNotExist:
            raise CustomAPIException(IMAGE_OBJECT_NOT_FOUND)

        # 아이돌이면 검사 제외 (임시설정)
        if data["object_type"] != "idol":

            # 유저 클래스면 같은 유저 인지
            if isinstance(target_instance, request.user.__class__):
                if target_instance != request.user:
                    raise CustomAPIException(IMAGE_NO_PERMISSION)
            # 작성자가 존재하면 작성자와 유저가 같은지
            elif hasattr(target_instance, "author"):
                if target_instance.author != request.user:
                    raise CustomAPIException(IMAGE_NO_PERMISSION)
            # 검사 실패
            else:
                raise CustomAPIException(IMAGE_CANNOT_VALIDATE_OWNERSHIP)

        data["content_type"] = content_type
        data["related_instance"] = target_instance
        return data

    def create(self, validated_data):
        image_urls = self.context["request"].data.getlist(
            "image_url"
        )  # URL로 온 이미지 주소
        image_files = self.context["request"].FILES.getlist("image")
        if not image_files and not image_urls:
            raise serializers.ValidationError(
                {"image": "이미지 파일 또는 url이 필요합니다."}
            )

        images = []

        # URL 업로드 처리
        for image_url in image_urls:
            image_url, public_id = upload_to_cloudinary(
                image_url, folder=validated_data["object_type"]
            )
            images.append(
                Image(
                    image_url=image_url,
                    public_id=public_id,
                    content_type=validated_data["content_type"],
                    object_id=validated_data["object_id"],
                )
            )

        for image_file in image_files:
            image_url, public_id = upload_to_cloudinary(
                image_file, folder=validated_data["object_type"]
            )
            images.append(
                Image(
                    image_url=image_url,
                    public_id=public_id,
                    content_type=validated_data["content_type"],
                    object_id=validated_data["object_id"],
                )
            )

        # bulk_create
        return Image.objects.bulk_create(images)

    def update(self, instance, validated_data):
        """
        기존 이미지들 삭제 후 새로운 이미지 등록
        """
        content_type = validated_data["content_type"]
        object_id = validated_data["object_id"]

        # 기존 이미지 삭제
        existing_images = Image.objects.filter(
            content_type=content_type, object_id=object_id
        )
        for image in existing_images:
            delete_from_cloudinary(image.public_id)
        existing_images.delete()

        # 새로 업로드
        return self.create(validated_data)

    def delete(self):
        """
        해당 모델 + object_id의 이미지 전부 삭제
        """
        validated_data = self.validated_data
        content_type = validated_data["content_type"]
        object_id = validated_data["object_id"]

        images = Image.objects.filter(content_type=content_type, object_id=object_id)
        for image in images:
            delete_from_cloudinary(image.public_id)
        count, _ = images.delete()
        return count
