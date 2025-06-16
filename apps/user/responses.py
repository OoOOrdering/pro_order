# 사용자 앱의 응답 메시지를 정의합니다.

# 이메일 관련 응답
DUPLICATE_EMAIL = {
    "code": 400,
    "message": "이미 사용 중인 이메일입니다.",
}

EMAIL_ALREADY_VERIFIED = {
    "code": 400,
    "message": "이미 인증된 이메일입니다.",
}

EMAIL_NOT_VERIFIED = {
    "code": 403,
    "message": "이메일 인증이 필요합니다.",
}

EMAIL_SEND_FAILED = {
    "code": 500,
    "message": "이메일 전송에 실패했습니다.",
}

# 토큰 관련 응답
INVALID_SIGNATURE = {
    "code": 400,
    "message": "유효하지 않은 서명입니다.",
}

SIGNATURE_EXPIRED = {
    "code": 410,
    "message": "만료된 서명입니다.",
}

INVALID_TOKEN = {
    "code": 400,
    "message": "유효하지 않은 토큰입니다.",
}

TOKEN_EXPIRED = {
    "code": 410,
    "message": "만료된 토큰입니다.",
}

# 사용자 관련 응답
USER_NOT_FOUND = {
    "code": 404,
    "message": "사용자를 찾을 수 없습니다.",
}

DUPLICATE_NICKNAME = {
    "code": 400,
    "message": "이미 사용 중인 닉네임입니다.",
}

INVALID_PASSWORD = {
    "code": 400,
    "message": "잘못된 비밀번호입니다.",
}

WEAK_PASSWORD = {
    "code": 400,
    "message": "비밀번호가 너무 약합니다.",
}

PASSWORD_MISMATCH = {
    "code": 400,
    "message": "비밀번호가 일치하지 않습니다.",
}

ACCOUNT_DEACTIVATED = {
    "code": 403,
    "message": "비활성화된 계정입니다.",
}

# 서버 관련 응답
SERVER_ERROR = {
    "code": 500,
    "message": "서버 오류가 발생했습니다.",
}

# 성공 관련 응답
SIGNUP_SUCCESS = {
    "code": 201,
    "message": "회원가입이 완료되었습니다.",
}

LOGIN_SUCCESS = {
    "code": 200,
    "message": "로그인이 완료되었습니다.",
}

LOGOUT_SUCCESS = {
    "code": 200,
    "message": "로그아웃이 완료되었습니다.",
}

PASSWORD_CHANGE_SUCCESS = {
    "code": 200,
    "message": "비밀번호가 변경되었습니다.",
}

PASSWORD_RESET_SUCCESS = {
    "code": 200,
    "message": "비밀번호 재설정 이메일이 전송되었습니다.",
}

PASSWORD_RESET_CONFIRM_SUCCESS = {
    "code": 200,
    "message": "비밀번호가 재설정되었습니다.",
}

PROFILE_UPDATE_SUCCESS = {
    "code": 200,
    "message": "프로필이 업데이트되었습니다.",
}

ACCOUNT_DEACTIVATE_SUCCESS = {
    "code": 200,
    "message": "계정이 비활성화되었습니다.",
}

EMAIL_VERIFICATION_SUCCESS = {
    "code": 200,
    "message": "이메일 인증이 완료되었습니다.",
}

EMAIL_VERIFICATION_RESEND_SUCCESS = {
    "code": 200,
    "message": "이메일 인증 메일이 재전송되었습니다.",
}

# 기타 응답
INVALID_REQUEST = {
    "code": 400,
    "message": "잘못된 요청입니다.",
}

UNAUTHORIZED = {
    "code": 401,
    "message": "인증되지 않은 사용자입니다.",
}

FORBIDDEN = {
    "code": 403,
    "message": "접근 권한이 없습니다.",
}

NOT_FOUND = {
    "code": 404,
    "message": "요청한 리소스를 찾을 수 없습니다.",
}

METHOD_NOT_ALLOWED = {
    "code": 405,
    "message": "허용되지 않은 메소드입니다.",
}

TOO_MANY_REQUESTS = {
    "code": 429,
    "message": "너무 많은 요청이 발생했습니다.",
}

INTERNAL_SERVER_ERROR = {
    "code": 500,
    "message": "서버 내부 오류가 발생했습니다.",
}

SERVICE_UNAVAILABLE = {
    "code": 503,
    "message": "서비스가 일시적으로 사용할 수 없습니다.",
}
