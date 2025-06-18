import logging
import os
import uuid
from io import BytesIO

import cloudinary
import cloudinary.api
import cloudinary.uploader
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from PIL import Image as PILImage

logger = logging.getLogger(__name__)

cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
)


def validate_image(image_file, max_size_mb=5):
    """
    이미지 파일 유효성 검사.

    Args:
    ----
        image_file: 업로드된 이미지 파일
        max_size_mb: 최대 허용 크기(MB)

    Returns:
    -------
        bool: 유효성 검사 통과 여부

    """
    try:
        # 파일 크기 검사
        if image_file.size > max_size_mb * 1024 * 1024:
            return False, f"이미지 크기는 {max_size_mb}MB를 초과할 수 없습니다."

        # 이미지 형식 검사
        img = PILImage.open(image_file)
        if img.format.lower() not in ["jpeg", "jpg", "png", "gif"]:
            return False, "지원하지 않는 이미지 형식입니다."

        return True, None
    except Exception as e:
        logger.error(f"이미지 검증 중 오류 발생: {e!s}")
        return False, "이미지 파일이 손상되었습니다."


def optimize_image(image_file, max_size=(800, 800), quality=85):
    """
    이미지 최적화.

    Args:
    ----
        image_file: 업로드된 이미지 파일
        max_size: 최대 크기 (width, height)
        quality: JPEG 품질 (1-100)

    Returns:
    -------
        BytesIO: 최적화된 이미지

    """
    try:
        img = PILImage.open(image_file)

        # 이미지 크기 조정
        if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
            img.thumbnail(max_size, PILImage.Resampling.LANCZOS)

        # 이미지 저장
        output = BytesIO()
        img.save(output, format=img.format, quality=quality, optimize=True)
        output.seek(0)

        return output
    except Exception as e:
        logger.error(f"이미지 최적화 중 오류 발생: {e!s}")
        raise


def generate_unique_filename(original_filename):
    """
    고유한 파일명을 생성합니다.

    Args:
    ----
        original_filename (str): 원본 파일명

    Returns:
    -------
        str: 고유한 파일명

    """
    ext = os.path.splitext(original_filename)[1]
    return f"{uuid.uuid4().hex}{ext}"


def compress_image(image_file, max_size=(800, 800)):
    """
    이미지를 압축합니다.

    Args:
    ----
        image_file (File): 압축할 이미지 파일
        max_size (tuple, optional): 최대 크기. Defaults to (800, 800).

    Returns:
    -------
        bytes: 압축된 이미지 데이터

    """
    img = PILImage.open(image_file)
    img.thumbnail(max_size, PILImage.Resampling.LANCZOS)
    return img


def save_image_to_storage(image_file, folder="images"):
    """
    이미지를 스토리지에 저장합니다.

    Args:
    ----
        image_file (File): 저장할 이미지 파일
        folder (str, optional): 저장할 폴더. Defaults to "images".

    Returns:
    -------
        tuple: (저장된 파일 경로, 파일명)

    """
    filename = generate_unique_filename(image_file.name)
    path = os.path.join(folder, filename)
    default_storage.save(path, ContentFile(image_file.read()))
    return path, filename


def upload_to_cloudinary(image_file, folder="images"):
    """
    이미지를 Cloudinary에 업로드합니다.

    Args:
    ----
        image_file (File): 업로드할 이미지 파일
        folder (str, optional): 업로드할 폴더. Defaults to "images".

    Returns:
    -------
        tuple: (이미지 URL, public_id)

    """
    result = cloudinary.uploader.upload(
        image_file,
        folder=folder,
        resource_type="image",
        transformation=[
            {"width": 800, "height": 800, "crop": "limit"},
            {"quality": "auto"},
        ],
    )
    return result["secure_url"], result["public_id"]


def delete_from_cloudinary(public_id):
    """
    Cloudinary에서 이미지를 삭제합니다.

    Args:
    ----
        public_id (str): 삭제할 이미지의 public_id

    """
    cloudinary.uploader.destroy(public_id)


def get_cloudinary_url(public_id, transformation=None):
    """
    Cloudinary URL 생성.

    Args:
    ----
        public_id: 이미지의 public_id
        transformation: Cloudinary 변환 옵션

    Returns:
    -------
        str: Cloudinary URL

    """
    try:
        return cloudinary.CloudinaryImage(public_id).build_url(transformation=transformation)
    except Exception as e:
        logger.error(f"Cloudinary URL 생성 중 오류 발생: {e!s}")
        raise


def generate_thumbnail_url(image_url: str, width: int = 300, height: int = 300, crop: str = "fill") -> str:
    """
    이미지 URL을 썸네일 URL로 변환합니다.

    Args:
    ----
        image_url (str): 원본 이미지 URL
        width (int, optional): 썸네일 너비. 기본값 300.
        height (int, optional): 썸네일 높이. 기본값 300.
        crop (str, optional): 자르기 방식. 기본값 "fill".

    Returns:
    -------
        str: 썸네일 URL

    """
    try:
        # Cloudinary URL 형식인 경우
        if "cloudinary.com" in image_url:
            # URL에서 변환 파라미터 추가
            if "?" in image_url:
                return f"{image_url}&w={width}&h={height}&c={crop}"
            return f"{image_url}?w={width}&h={height}&c={crop}"
        return image_url
    except Exception as e:
        logger.error(f"Error generating thumbnail URL: {e}")
        return image_url


# # 업로드 시
# image_file = request.FILES.get("image")
# if image_file:
#     image_url, public_id = upload_to_cloudinary(image_file, folder="posts")
#     post.image_url = image_url
#     post.image_public_id = public_id

# 폴더 이름은 앱 이름이나 목적별로 구분하는 것이 좋습니다 (예: "profiles", "idols", "posts")
# 에러 발생 시 서비스 로직을 중단하지 않게 try-except로 감싸는 것도 권장됩니다
# 나중에 이미지 삭제 시 public_id를 그대로 사용할 수 있습니다
