import logging
from io import BytesIO

import cloudinary
import cloudinary.uploader
from PIL import Image as PILImage

logger = logging.getLogger(__name__)


def validate_image(image_file, max_size_mb=5):
    """이미지 파일 유효성 검사.

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
    """이미지 최적화.

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


def upload_to_cloudinary(image_file, folder="images", transformation=None):
    """Cloudinary에 이미지 업로드.

    Args:
    ----
        image_file: 업로드할 이미지 파일
        folder: Cloudinary 폴더 경로
        transformation: Cloudinary 변환 옵션

    Returns:
    -------
        dict: 업로드 결과 (public_id, secure_url 등)

    """
    try:
        # 이미지 검증
        is_valid, error_message = validate_image(image_file)
        if not is_valid:
            raise ValueError(error_message)

        # 이미지 최적화
        optimized_image = optimize_image(image_file)

        # Cloudinary 업로드
        upload_result = cloudinary.uploader.upload(
            optimized_image,
            folder=folder,
            transformation=transformation,
            resource_type="image",
        )

        return {
            "public_id": upload_result["public_id"],
            "secure_url": upload_result["secure_url"],
            "format": upload_result["format"],
            "width": upload_result["width"],
            "height": upload_result["height"],
        }
    except Exception as e:
        logger.error(f"Cloudinary 업로드 중 오류 발생: {e!s}")
        raise


def delete_from_cloudinary(public_id):
    """Cloudinary에서 이미지 삭제.

    Args:
    ----
        public_id: 삭제할 이미지의 public_id

    """
    try:
        result = cloudinary.uploader.destroy(public_id)
        if result.get("result") != "ok":
            raise Exception(f"이미지 삭제 실패: {result.get('error', {}).get('message')}")
    except Exception as e:
        logger.error(f"Cloudinary 이미지 삭제 중 오류 발생: {e!s}")
        raise


def get_cloudinary_url(public_id, transformation=None):
    """Cloudinary URL 생성.

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


def generate_thumbnail_url(original_url, width=300, height=300, crop="fill"):
    """Cloudinary 이미지 URL을 기반으로 썸네일 URL을 생성합니다.

    Args:
    ----
        original_url (str): Cloudinary의 원본 secure_url
        width (int): 썸네일 너비
        height (int): 썸네일 높이
        crop (str): 자르기 방식 (fill, crop, thumb 등)

    Returns:
    -------
        str: 변환된 썸네일 이미지 URL

    """
    if not original_url or "/upload/" not in original_url:
        return original_url

    return original_url.replace("/upload/", f"/upload/w_{width},h_{height},c_{crop},q_auto,f_auto/")


# # 업로드 시
# image_file = request.FILES.get("image")
# if image_file:
#     image_url, public_id = upload_to_cloudinary(image_file, folder="posts")
#     post.image_url = image_url
#     post.image_public_id = public_id

# 폴더 이름은 앱 이름이나 목적별로 구분하는 것이 좋습니다 (예: "profiles", "idols", "posts")
# 에러 발생 시 서비스 로직을 중단하지 않게 try-except로 감싸는 것도 권장됩니다
# 나중에 이미지 삭제 시 public_id를 그대로 사용할 수 있습니다
