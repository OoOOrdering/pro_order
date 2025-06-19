import logging

from rest_framework.response import Response

# 공통 응답 상수 정의
SIGNUP_SUCCESS = {"code": 201, "message": "회원가입에 성공했습니다."}
SIGNUP_PASSWORD_MISMATCH = {"code": 400, "message": "비밀번호가 일치하지 않습니다."}
WEAK_PASSWORD = {"code": 400, "message": "비밀번호가 너무 약합니다."}
VERIFY_EMAIL_SUCCESS = {"code": 200, "message": "이메일 인증에 성공했습니다."}
INVALID_SIGNATURE = {"code": 400, "message": "유효하지 않은 서명입니다."}
SIGNATURE_EXPIRED = {"code": 410, "message": "서명이 만료되었습니다."}
VERIFY_EMAIL_ALREADY_VERIFIED = {"code": 400, "message": "이미 인증된 이메일입니다."}
EMAIL_SEND_FAILED = {"code": 500, "message": "이메일 전송에 실패했습니다."}
LOGIN_FAILED = {"code": 401, "message": "로그인에 실패했습니다."}
LOGIN_SUCCESS = {"code": 200, "message": "로그인에 성공했습니다."}
LOGOUT_SUCCESS = {"code": 200, "message": "로그아웃에 성공했습니다."}
MISSING_REFRESH_TOKEN = {"code": 401, "message": "리프레시 토큰이 누락되었습니다."}
INVALID_REFRESH_TOKEN = {"code": 401, "message": "유효하지 않은 리프레시 토큰입니다."}
PASSWORD_CHANGED = {"code": 200, "message": "비밀번호가 변경되었습니다."}
PROFILE_RETRIEVE_RESPONSE = {"code": 200, "message": "프로필 조회에 성공했습니다."}
PROFILE_UPDATE_RESPONSE = {"code": 200, "message": "프로필 업데이트에 성공했습니다."}
INVALID_PROFILE_UPDATE = {"code": 400, "message": "프로필 업데이트에 실패했습니다."}
UNAUTHORIZED = {"code": 401, "message": "인증되지 않은 사용자입니다."}
SERVER_ERROR = {"code": 500, "message": "서버 오류가 발생했습니다."}
DUPLICATE_NICKNAME = {"code": 400, "message": "이미 사용 중인 닉네임입니다."}
CSRF_INVALID_TOKEN = {"code": 403, "message": "CSRF 토큰이 유효하지 않습니다."}
TOKEN_REFRESH_RESPONSE = {"code": 200, "message": "토큰이 갱신되었습니다."}
UPLOAD_SUCCESS = {"code": 201, "message": "이미지 업로드에 성공했습니다."}

logger = logging.getLogger(__name__)


class BaseResponseMixin:
    logger = logging.getLogger("apps")

    def success(self, data=None, message="성공", code=200, status=200):
        self.logger.info(f"SUCCESS: {message}")
        return Response({"success": True, "code": code, "message": message, "data": data}, status=status)

    def error(self, message="오류", code=400, status=400, data=None):
        self.logger.warning(f"ERROR: {message}")
        return Response({"success": False, "code": code, "message": message, "data": data}, status=status)
