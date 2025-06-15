import cloudinary.uploader
from cloudinary.exceptions import Error as CloudinaryError


def upload_to_cloudinary(file, folder="uploads"):
    """
    Cloudinary에 이미지를 업로드하고 URL과 public_id를 반환합니다.

    Args:
        file: Django의 UploadedFile 객체
        folder (str): Cloudinary 폴더 경로

    Returns:
        (image_url, public_id): 업로드된 이미지의 URL과 식별자
    """
    try:
        result = cloudinary.uploader.upload(
            file, folder=folder, format="webp", resource_type="image"
        )
        return result["secure_url"], result["public_id"]

    except CloudinaryError as e:
        raise RuntimeError(f"Cloudinary 업로드 실패: {str(e)}")


def generate_thumbnail_url(original_url, width=300, height=300, crop="fill"):
    """
    Cloudinary 이미지 URL을 기반으로 썸네일 URL을 생성합니다.

    Args:
        original_url (str): Cloudinary의 원본 secure_url
        width (int): 썸네일 너비
        height (int): 썸네일 높이
        crop (str): 자르기 방식 (fill, crop, thumb 등)

    Returns:
        str: 변환된 썸네일 이미지 URL
    """
    if not original_url or "/upload/" not in original_url:
        return original_url  # fallback

    return original_url.replace("/upload/", f"/upload/w_{width},h_{height},c_{crop}/")


def delete_from_cloudinary(public_id):
    """
    Cloudinary에서 public_id를 통해 이미지 삭제

    Args:
        public_id (str): 삭제할 이미지의 Cloudinary public_id

    Returns:
        dict: Cloudinary 삭제 응답 (e.g., {'result': 'ok'})
    """
    if not public_id:
        return {"result": "no public_id"}

    try:
        result = cloudinary.uploader.destroy(public_id)
        return result
    except CloudinaryError as e:
        raise RuntimeError(f"Cloudinary 삭제 실패: {str(e)}")


# # 업로드 시
# image_file = request.FILES.get("image")
# if image_file:
#     image_url, public_id = upload_to_cloudinary(image_file, folder="posts")
#     post.image_url = image_url
#     post.image_public_id = public_id

# 폴더 이름은 앱 이름이나 목적별로 구분하는 것이 좋습니다 (예: "profiles", "idols", "posts")
# 에러 발생 시 서비스 로직을 중단하지 않게 try-except로 감싸는 것도 권장됩니다
# 나중에 이미지 삭제 시 public_id를 그대로 사용할 수 있습니다
