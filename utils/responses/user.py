# fmt: off

# 회원가입
SIGNUP_SUCCESS = {
    "code": 201,
    "message": "회원가입이 완료되었습니다.",
    "data": None,
}
SIGNUP_FAILED = {
    "code": 200,
    "message": "회원가입을 실패하였습니다.",
    "data": None,
}
SIGNUP_PASSWORD_MISMATCH = {
    "code": 400,
    "message": "비밀번호가 일치하지 않습니다.",
    "data": None,
}
WEAK_PASSWORD = {
    "code": 400,
    "message": "비밀번호가 보안 기준을 만족하지 않습니다.",
    "data": None,
}
DUPLICATE_EMAIL = {
    "code": 400,
    "message": "이미 존재하는 이메일입니다.",
    "data": None
}

DUPLICATE_NICKNAME = {
    "code": 400,
    "message": "이미 존재하는 닉네임입니다.",
    "data": None
}

# EMAIL_NOT_VERIFIED = {
#     "code": 400,
#     "message": "이메일 인증이 완료되지 않았습니다.",
#     "data": None
# }
# SOCIAL_LOGIN_FAILED = {
#     "code": 400,
#     "message": "소셜 로그인에 실패했습니다.",
#     "data": None
# }


# 이메일 인증
VERIFY_EMAIL_SUCCESS = {
    "code": 200,
    "message": "이메일 인증이 완료되었습니다.",
    "data": {
        "verified": True
    },
}
VERIFY_EMAIL_ALREADY_VERIFIED = {
    "code": 200,
    "message": "이미 인증된 이메일입니다.",
    "data": {
        "verified": True
    },
}
SIGNATURE_EXPIRED = {
    "code": 410,
    "message": "인증 링크가 만료되었습니다.",
    "data": None,
}
INVALID_SIGNATURE = {
    "code": 400,
    "message": "유효하지 않은 인증 코드입니다.",
    "data": None,
}


# 비밀번호 확인
PASSWORD_MATCH_SUCCESS = {
    "code": 200,
    "message": "비밀번호가 일치합니다.",
    "data": {"matched": True},
}

PASSWORD_NOT_MATCH = {
    "code": 400,
    "message": "비밀번호가 일치하지 않습니다.",
    "data": {"matched": False},
}

PASSWORD_CHECK_INVALID = {
    "code": 400,
    "message": "입력값이 유효하지 않습니다.",
    "data": None,  # 또는 추후 serializer.errors를 덮어쓸 예정이면 None
}

# 로그인 로그아웃
LOGIN_SUCCESS = {
    "code": 200,
    "message": "로그인을 성공했습니다.",
}
LOGIN_FAILED = {
    "code": 401,
    "message": "이메일 또는 비밀번호가 올바르지 않습니다.",
    "data": None,
}
LOGOUT_SUCCESS = {
    "code": 200,
    "message": "로그아웃되었습니다.",
    "data": None,
}

# CSRF토큰
CSRF_VALIDATION_FAILED = {
    "code": 403,
    "message": "CSRF 검증을 실패했습니다",
    "data": None,
}
CSRF_INVALID_TOKEN = {
    "code": 403,
    "message": "유효하지 않은 CSRF 토큰입니다.",
    "data": None,
}

# Refresh 토큰
INVALID_REFRESH_TOKEN = {
    "code": 401,
    "message": "유효하지 않은 리프레시 토큰입니다.",
    "data": None,
}
MISSING_REFRESH_TOKEN = {
    "code": 401,
    "message": "리프레시 토큰이 없습니다.",
    "data": None,
}
TOKEN_REFRESH_RESPONSE = {
    "code": 200,
    "message": "액세스 토큰이 재발급되었습니다.",
    "data": None,
}

# 프로필 조회
PROFILE_RETRIEVE_RESPONSE = {
    "code": 200,
    "message": "프로필 정보를 불러왔습니다.",
}
# 프로필 수정 성공
PROFILE_UPDATE_RESPONSE = {
    "code": 200,
    "message": "회원정보가 수정되었습니다.",
}
# 프로필 수정 실패
INVALID_PROFILE_UPDATE = {
    "code": 400,
    "message": "유효하지 않은 입력입니다.",
}
# 회원 탈퇴 성공
PROFILE_DELETE_RESPONSE = {
    "code": 200,
    "message": "회원 탈퇴가 완료되었습니다.",
    "data": None,
}

# 인증 실패
UNAUTHORIZED_RESPONSE = {
    "code": 401,
    "message": "인증 정보가 없습니다.",
    "data": None,
}

# 인증 관련
NOT_AUTHENTICATED = {
    "code": 401,
    "message": "로그인이 필요한 서비스입니다.",
    "data": None,
}


# ValidationError	유효성 검증 실패	400
# NotAuthenticated	인증 안 됨	401
# PermissionDenied	권한 없음	403
# NotFound	리소스 없음	404
# APIException	기본 Exception (상태코드 500)	500
