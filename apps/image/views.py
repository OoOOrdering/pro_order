from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from utils.responses.image import UPLOAD_SUCCESS

from .serializers import ImageUploadSerializer


class ImageUploadView(GenericAPIView):
    serializer_class = ImageUploadSerializer
    permission_classes = [IsAuthenticated]  # 인증된 사용자만 데이터 접근 가능
    authentication_classes = [JWTAuthentication]  # JWT 인증
    parser_classes = [MultiPartParser, FormParser]

    # def get_serializer_class(self):
    #     pass

    @swagger_auto_schema(
        tags=["이미지"],
        operation_summary="이미지 업로드",
        operation_description="이미지를 업로드하고 썸네일을 생성합니다.",
        request_body=ImageUploadSerializer,
        responses={
            201: "업로드 성공",
            400: "유효하지 않은 요청",
        },
    )
    def post(self, request):
        serializer = self.get_serializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        images = serializer.save()
        custom_response = UPLOAD_SUCCESS
        custom_response["data"] = [
            {
                "image_url": image.image_url,
                "thumbnail_url": image.get_thumbnail_url(),
                "public_id": image.public_id,
            }
            for image in images
        ]
        return Response(custom_response, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        tags=["이미지"],
        operation_summary="이미지 삭제",
        operation_description="업로드된 이미지를 삭제합니다.",
        request_body=ImageUploadSerializer,
        responses={
            200: "삭제 성공",
            400: "삭제 실패 또는 잘못된 요청",
        },
    )
    def delete(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        deleted_count = serializer.delete()
        return Response(
            {
                "code": 200,
                "message": f"{deleted_count}개의 이미지가 삭제되었습니다.",
                "data": {"deleted": True, "deleted_count": deleted_count},
            },
            status=status.HTTP_200_OK,
        )
