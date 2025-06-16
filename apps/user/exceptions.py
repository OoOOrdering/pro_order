from rest_framework import status
from rest_framework.exceptions import APIException

from apps.user.responses import (
    DUPLICATE_EMAIL,
    EMAIL_ALREADY_VERIFIED,
    INVALID_SIGNATURE,
    SERVER_ERROR,
    SIGNATURE_EXPIRED,
    USER_NOT_FOUND,
)


class CustomAPIException(APIException):
    def __init__(self, detail, code=None):
        if isinstance(detail, dict):
            self.detail = detail.get("message", "오류 발생")
            self.status_code = detail.get("code", status.HTTP_400_BAD_REQUEST)
        else:
            self.detail = detail
            self.status_code = code if code is not None else status.HTTP_400_BAD_REQUEST


class UserNotFoundError(CustomAPIException):
    def __init__(self):
        super().__init__(USER_NOT_FOUND)


class InvalidTokenError(CustomAPIException):
    def __init__(self, message=INVALID_SIGNATURE["message"]):
        super().__init__(message, code=INVALID_SIGNATURE["code"])


class TokenExpiredError(CustomAPIException):
    def __init__(self):
        super().__init__(SIGNATURE_EXPIRED)


class EmailAlreadyVerifiedError(CustomAPIException):
    def __init__(self):
        super().__init__(EMAIL_ALREADY_VERIFIED)


class DuplicateEmailError(CustomAPIException):
    def __init__(self):
        super().__init__(DUPLICATE_EMAIL)


class DuplicateNicknameError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "이미 사용 중인 닉네임입니다."
    default_code = "duplicate_nickname"


class InvalidPasswordError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "잘못된 비밀번호입니다."
    default_code = "invalid_password"


class AccountDeactivatedError(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "비활성화된 계정입니다."
    default_code = "account_deactivated"


class EmailNotVerifiedError(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "이메일 인증이 필요합니다."
    default_code = "email_not_verified"


class ServerError(CustomAPIException):
    def __init__(self):
        super().__init__(SERVER_ERROR)
