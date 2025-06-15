UPLOAD_SUCCESS = {
    "code": 201,
    "message": "업로드가 완료되었습니다.",
    "data": None,
}

IMAGE_REQUEST_MISSING = {"code": 400, "message": "요청 정보가 없습니다.", "data": None}

# ===== 이미지 관련 =====
IMAGE_INVALID_MODEL = {
    "code": 400,
    "message": "유효하지 않은 모델입니다.",
    "data": None,
}

IMAGE_OBJECT_NOT_FOUND = {
    "code": 400,
    "message": "해당 객체가 존재하지 않습니다.",
    "data": None,
}


IMAGE_NO_PERMISSION = {
    "code": 403,
    "message": "해당 객체에 대한 권한이 없습니다.",
    "data": None,
}

IMAGE_CANNOT_VALIDATE_OWNERSHIP = {
    "code": 400,
    "message": "권한 검사를 수행할 수 없는 객체입니다.",
    "data": None,
}
