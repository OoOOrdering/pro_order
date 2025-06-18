import logging
from datetime import timedelta
from smtplib import SMTPException

# Django imports
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import signing
from django.core.signing import SignatureExpired, TimestampSigner
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from django.utils import timezone

# Third-party imports
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.user.models import User
from apps.user.serializers import (
    EmailVerificationSerializer,
    LogoutSerializer,
    PasswordChangeSerializer,
    PasswordResetConfirmSerializer,
    ProfileUpdateSerializer,
    RegisterSerializer,
    ResendVerificationEmailSerializer,
    UserBulkApproveSerializer,
    UserSerializer,
)
from apps.user.throttles import LoginAttemptThrottle
from utils.csrf import generate_csrf_token, validate_csrf_token
from utils.email import send_email

# Local app imports
from .exceptions import CustomAPIException, DuplicateEmailError, DuplicateNicknameError, ServerError, UserNotFoundError


# Helper functions for consistent API responses
def success_response(message="Success", data=None, code=status.HTTP_200_OK):
    return Response({"code": code, "message": message, "data": data}, status=code)


def error_response(message="Error", data=None, code=status.HTTP_400_BAD_REQUEST):
    return Response({"code": code, "message": message, "data": data}, status=code)


# Response constants
CSRF_INVALID_TOKEN = {"code": 403, "message": "CSRF 토큰이 유효하지 않습니다."}
EMAIL_SEND_FAILED = {"code": 500, "message": "이메일 전송에 실패했습니다."}
INVALID_PROFILE_UPDATE = {"code": 400, "message": "프로필 업데이트에 실패했습니다."}
PASSWORD_NOT_MATCH = {"code": 400, "message": "비밀번호가 일치하지 않습니다."}
INVALID_REFRESH_TOKEN = {"code": 401, "message": "유효하지 않은 리프레시 토큰입니다."}
INVALID_SIGNATURE = {"code": 400, "message": "유효하지 않은 서명입니다."}
LOGIN_FAILED = {"code": 401, "message": "로그인에 실패했습니다."}
LOGIN_SUCCESS = {"code": 200, "message": "로그인에 성공했습니다."}
LOGOUT_SUCCESS = {"code": 200, "message": "로그아웃에 성공했습니다."}
MISSING_REFRESH_TOKEN = {"code": 401, "message": "리프레시 토큰이 누락되었습니다."}
PASSWORD_CHANGED = {"code": 200, "message": "비밀번호가 변경되었습니다."}
PROFILE_RETRIEVE_RESPONSE = {"code": 200, "message": "프로필 조회에 성공했습니다."}
PROFILE_UPDATE_RESPONSE = {"code": 200, "message": "프로필 업데이트에 성공했습니다."}
UNAUTHORIZED = {"code": 401, "message": "인증되지 않은 사용자입니다."}
SERVER_ERROR = {"code": 500, "message": "서버 오류가 발생했습니다."}
SIGNATURE_EXPIRED = {"code": 410, "message": "서명이 만료되었습니다."}
SIGNUP_PASSWORD_MISMATCH = {"code": 400, "message": "비밀번호가 일치하지 않습니다."}
SIGNUP_SUCCESS = {"code": 201, "message": "회원가입에 성공했습니다."}
TOKEN_REFRESH_RESPONSE = {"code": 200, "message": "토큰이 갱신되었습니다."}
VERIFY_EMAIL_ALREADY_VERIFIED = {"code": 400, "message": "이미 인증된 이메일입니다."}
VERIFY_EMAIL_SUCCESS = {"code": 200, "message": "이메일 인증에 성공했습니다."}
WEAK_PASSWORD = {"code": 400, "message": "비밀번호가 너무 약합니다."}

logger = logging.getLogger("apps")

User = get_user_model()


# 회원 가입
class RegisterView(CreateAPIView):
    """
    회원가입 API.

    새로운 사용자를 생성하고, 이메일 인증을 위한 이메일을 전송합니다.
    """

    queryset = User.objects.all()  # Model
    serializer_class = RegisterSerializer  # Serializer

    @swagger_auto_schema(
        tags=["유저"],
        operation_summary="회원가입",
        operation_description="새로운 사용자를 생성하고, 이메일 인증을 위한 이메일을 전송합니다.",
        request_body=RegisterSerializer,
        responses={
            201: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "code": openapi.Schema(type=openapi.TYPE_INTEGER, example=SIGNUP_SUCCESS["code"]),
                    "message": openapi.Schema(type=openapi.TYPE_STRING, example=SIGNUP_SUCCESS["message"]),
                    "data": openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "id": openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
                            "email": openapi.Schema(type=openapi.TYPE_STRING, example="test@example.com"),
                            "name": openapi.Schema(type=openapi.TYPE_STRING, example="taejin"),
                            "nickname": openapi.Schema(type=openapi.TYPE_STRING, example="Lululala"),
                            "verify_url": openapi.Schema(
                                type=openapi.TYPE_STRING,
                                example="http://localhost:8000/api/users/verify/email?code=signed_code",
                            ),
                        },
                    ),
                },
            ),
            400: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "code": openapi.Schema(
                        type=openapi.TYPE_INTEGER,
                        example=SIGNUP_PASSWORD_MISMATCH["code"],
                    ),
                    "message": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        example=f"{SIGNUP_PASSWORD_MISMATCH['message']} or {WEAK_PASSWORD['message']}",
                    ),
                    "data": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        example='None or "This password is too short" or "It must contain at least 8 characters." or "This password is too common"',
                    ),
                },
            ),
        },
    )
    def post(self, request):  # 스웨거 데코레이터 사용하기 위해 오버라이드(원래 동작과 동일)
        return self.create(request)  # CreateAPIView가 내부적으로 사용하는 create 호출

    def create(self, request, *args, **kwargs):  # noqa: ARG002
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            user = serializer.save()

            signer = TimestampSigner()
            signed_email = signer.sign(user.email)
            signed_code = signing.dumps(signed_email)

            verify_url = f"{request.scheme}://{request.get_host()}/api/users/verify/email?code={signed_code}"

            subject = "[WiStar] 이메일 인증을 완료해주세요."
            message = f"아래 링크를 클릭해 인증을 완료해주세요.\n\n{verify_url}"
            send_email(subject, message, user.email)

            response_data = serializer.data
            custom_response = SIGNUP_SUCCESS

            if settings.DEBUG:
                response_data["verify_url"] = verify_url

            custom_response["data"] = response_data
            logger.info(f"User registered successfully: {user.email}")
            return success_response(
                message=SIGNUP_SUCCESS["message"],
                data=response_data,
                code=status.HTTP_201_CREATED,
            )
        except IntegrityError as e:
            if "email" in str(e):
                logger.warning(f"Registration failed due to duplicate email: {serializer.validated_data.get('email')}")
                raise DuplicateEmailError() from e
            elif "nickname" in str(e):
                logger.warning(
                    f"Registration failed due to duplicate nickname: {serializer.validated_data.get('nickname')}",
                )
                raise DuplicateNicknameError() from e
            else:
                logger.error(f"Database integrity error during registration: {e}", exc_info=True)
                raise ServerError() from e
        except SMTPException as e:
            logger.error(
                f"Email sending failed during registration for user {user.email}: {e}",
                exc_info=True,
            )
            raise CustomAPIException(EMAIL_SEND_FAILED) from e
        except Exception as e:
            logger.error(f"Unexpected error during user registration: {e}", exc_info=True)
            raise ServerError() from e


# 이메일 인증
class VerifyEmailView(APIView):
    """
    이메일 인증 API.

    사용자가 이메일 인증 링크를 클릭했을 때 호출됩니다.
    토큰을 검증하고 사용자의 이메일 인증 상태를 활성화합니다.
    """

    permission_classes = [AllowAny]

    @swagger_auto_schema(
        tags=["유저/인증"],
        operation_summary="이메일 인증 링크 확인",
        operation_description="이메일에 첨부된 서명된 인증 코드를 확인하여 이메일 인증을 완료합니다.",
        responses={
            200: openapi.Response(
                description="이메일 인증 성공",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "code": openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            example=VERIFY_EMAIL_SUCCESS["code"],
                        ),
                        "message": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example=VERIFY_EMAIL_SUCCESS["message"],
                        ),
                        "data": None,
                    },
                ),
            ),
            400: openapi.Response(
                description="유효하지 않은 서명",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "code": openapi.Schema(type=openapi.TYPE_INTEGER, example=INVALID_SIGNATURE["code"]),
                        "message": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example=INVALID_SIGNATURE["message"],
                        ),
                        "data": None,
                    },
                ),
            ),
            410: openapi.Response(
                description="인증 코드 만료",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "code": openapi.Schema(type=openapi.TYPE_INTEGER, example=SIGNATURE_EXPIRED["code"]),
                        "message": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example=SIGNATURE_EXPIRED["message"],
                        ),
                        "data": None,
                    },
                ),
            ),
        },
    )
    def get(self, request):
        code = request.query_params.get("code")
        if not code:
            logger.warning("Email verification failed: Missing code parameter.")
            return error_response(message=INVALID_SIGNATURE["message"])

        signer = TimestampSigner()
        try:
            signed_email = signing.loads(code, max_age=timedelta(minutes=settings.EMAIL_VERIFICATION_TIMEOUT_MINUTES))
            email = signer.unsign(signed_email)
            user = get_object_or_404(User, email=email)

            if user.is_email_verified:
                logger.info(f"Email verification failed: Email already verified for user {email}")
                return error_response(message=VERIFY_EMAIL_ALREADY_VERIFIED["message"])

            user.is_email_verified = True
            user.is_active = True
            user.save()
            logger.info(f"Email verified successfully for user {email}")
            return success_response(message=VERIFY_EMAIL_SUCCESS["message"])
        except SignatureExpired as e:
            logger.warning(f"Email verification failed: Signature expired. Code: {code}", exc_info=True)
            return error_response(message=SIGNATURE_EXPIRED["message"], code=SIGNATURE_EXPIRED["code"])
        except signing.BadSignature as e:
            logger.warning(f"Email verification failed: Invalid signature. Code: {code}", exc_info=True)
            return error_response(message=INVALID_SIGNATURE["message"], code=INVALID_SIGNATURE["code"])
        except User.DoesNotExist as e:
            logger.warning(f"Email verification failed: User not found for code {code}", exc_info=True)
            raise UserNotFoundError() from e
        except Exception as e:
            logger.error(f"Unexpected error during email verification GET: {e}", exc_info=True)
            raise ServerError() from e


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    JWT 로그인 API.

    이메일과 비밀번호를 사용하여 액세스 토큰과 리프레시 토큰을 발급합니다.
    리프레시 토큰은 HttpOnly 쿠키로 설정됩니다.
    """

    throttle_classes = [LoginAttemptThrottle]

    @swagger_auto_schema(
        tags=["유저"],
        operation_summary="JWT 로그인",
        operation_description="이메일과 비밀번호를 사용하여 액세스 토큰과 리프레시 토큰을 발급합니다. 리프레시 토큰은 HttpOnly 쿠키로 설정됩니다.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["email", "password"],
            properties={
                "email": openapi.Schema(type=openapi.TYPE_STRING, format="email"),
                "password": openapi.Schema(type=openapi.TYPE_STRING, format="password"),
            },
        ),
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "code": openapi.Schema(type=openapi.TYPE_INTEGER, example=LOGIN_SUCCESS["code"]),
                    "message": openapi.Schema(type=openapi.TYPE_STRING, example=LOGIN_SUCCESS["message"]),
                    "data": openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "access_token": openapi.Schema(type=openapi.TYPE_STRING),
                            "csrf_token": openapi.Schema(type=openapi.TYPE_STRING),
                        },
                    ),
                },
            ),
            401: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "code": openapi.Schema(type=openapi.TYPE_INTEGER, example=LOGIN_FAILED["code"]),
                    "message": openapi.Schema(type=openapi.TYPE_STRING, example=LOGIN_FAILED["message"]),
                },
            ),
            429: openapi.Response(
                description="요청이 너무 많음",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "detail": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="요청이 너무 많습니다. 300초 후에 다시 시도해주세요.",
                        ),
                    },
                ),
            ),
        },
    )
    def post(self, request, *args, **kwargs):
        # 부모 클래스의 post 메서드 호출
        response = super().post(request, *args, **kwargs)

        if response.status_code == status.HTTP_200_OK:
            try:
                user = User.objects.get(email=request.data["email"])
                user.last_login = timezone.now()
                user.save()
            except User.DoesNotExist as e:
                logger.error(f"User not found after successful login for email: {request.data['email']}", exc_info=True)
                raise ServerError() from e
            except Exception as e:
                logger.error(f"Error updating last_login for user {request.data['email']}: {e}", exc_info=True)
                raise ServerError() from e

            # 리프레시 토큰을 HttpOnly 쿠키에 설정
            refresh_token = response.data["refresh"]
            response.set_cookie(
                key=settings.SIMPLE_JWT["REFRESH_TOKEN_NAME"],
                value=refresh_token,
                httponly=True,
                samesite="Lax",  # CSRF 보호를 위해 'Lax' 또는 'Strict' 설정
                secure=True,  # HTTPS 환경에서만 전송
                max_age=settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds(),
            )
            del response.data["refresh"]

            # CSRF 토큰 생성 및 응답 데이터에 포함
            csrf_token = generate_csrf_token(request)
            response.data["csrf_token"] = csrf_token

            logger.info(f"User logged in successfully: {request.data['email']}")
            return success_response(
                message=LOGIN_SUCCESS["message"],
                data={"access_token": response.data["access"], "csrf_token": csrf_token},
                code=status.HTTP_200_OK,
            )
        else:
            logger.warning(
                f"Login failed for user {request.data.get('email')}: {response.status_code} - {response.data}"
            )
            return error_response(message=LOGIN_FAILED["message"], code=status.HTTP_401_UNAUTHORIZED)


class LogoutAPIView(APIView):
    """
    JWT 로그아웃 API.

    리프레시 토큰을 블랙리스트에 추가하고, HttpOnly 쿠키에서 리프레시 토큰을 삭제합니다.
    """

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=["유저"],
        operation_summary="JWT 로그아웃",
        operation_description="로그아웃 시 HttpOnly 쿠키에 저장된 리프레시 토큰을 블랙리스트에 등록하고, 쿠키에서 삭제합니다.",
        request_body=None,
        responses={
            200: openapi.Response(
                description="로그아웃 성공",
                type=openapi.TYPE_OBJECT,
                properties={
                    "code": openapi.Schema(type=openapi.TYPE_INTEGER, example=LOGOUT_SUCCESS["code"]),
                    "message": openapi.Schema(type=openapi.TYPE_STRING, example=LOGOUT_SUCCESS["message"]),
                    "data": None,
                },
            ),
            401: openapi.Response(
                description="리프레시 토큰이 누락되었거나 유효하지 않음",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "code": openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            example=MISSING_REFRESH_TOKEN["code"],
                        ),
                        "message": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example=f"{MISSING_REFRESH_TOKEN['message']} or {INVALID_REFRESH_TOKEN['message']}",
                        ),
                        "data": None,
                    },
                ),
            ),
        },
    )
    def post(self, request, *args, **kwargs):  # noqa: ARG002
        refresh_token = request.COOKIES.get(settings.SIMPLE_JWT["REFRESH_TOKEN_NAME"])
        if not refresh_token:
            logger.warning("Logout failed: Refresh token not found in cookies.")
            return error_response(message=MISSING_REFRESH_TOKEN["message"], code=MISSING_REFRESH_TOKEN["code"])
        serializer = LogoutSerializer(data={"refresh_token": refresh_token})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        response = success_response(message=LOGOUT_SUCCESS["message"])
        response.delete_cookie(settings.SIMPLE_JWT["REFRESH_TOKEN_NAME"])  # HttpOnly 쿠키 삭제
        logger.info(f"User {request.user.email} logged out successfully.")
        return response


class CustomTokenRefreshView(APIView):
    @swagger_auto_schema(
        tags=["유저"],
        operation_summary="액세스 토큰 재발급",
        operation_description="HttpOnly 쿠키에 저장된 리프레시 토큰으로 새로운 액세스 토큰과 CSRF 토큰을 재발급합니다.",
        request_body=None,
        manual_parameters=[
            openapi.Parameter(
                name="X-CSRFToken",
                in_=openapi.IN_HEADER,
                type=openapi.TYPE_STRING,
                description="CSRF 토큰",
                required=True,
                example="yJhbGciOiJIUzI1NiIs...",
            ),
        ],
        responses={
            200: openapi.Response(
                description="토큰 재발급 성공",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "code": openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            example=TOKEN_REFRESH_RESPONSE["code"],
                        ),
                        "message": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example=TOKEN_REFRESH_RESPONSE["message"],
                        ),
                        "data": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "access_token": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                                ),
                                "csrf_token": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="newly_generated_csrf_token_abc123",
                                ),
                            },
                        ),
                    },
                ),
            ),
            401: openapi.Response(
                description="리프레시 토큰이 누락되었거나 유효하지 않음",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "code": openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            example=MISSING_REFRESH_TOKEN["code"],
                        ),
                        "message": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example=MISSING_REFRESH_TOKEN["message"],
                        ),
                        "data": None,
                    },
                ),
            ),
            403: openapi.Response(
                description="CSRF 토큰이 누락되었거나 유효하지 않음",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "code": openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            example=CSRF_INVALID_TOKEN["code"],
                        ),
                        "message": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example=CSRF_INVALID_TOKEN["message"],
                        ),
                        "data": None,
                    },
                ),
            ),
        },
    )
    def post(self, request):
        # CSRF 토큰 검증
        csrf_token_header = request.headers.get("X-CSRFToken")
        if not validate_csrf_token(request, csrf_token_header):
            logger.warning(f"Token refresh failed: Invalid CSRF token for user {request.user.email}")
            return error_response(message=CSRF_INVALID_TOKEN["message"], code=CSRF_INVALID_TOKEN["code"])

        # 리프레시 토큰 추출
        refresh_token = request.COOKIES.get(settings.SIMPLE_JWT["REFRESH_TOKEN_NAME"])
        if not refresh_token:
            logger.warning("Token refresh failed: Missing refresh token in cookies.")
            return error_response(message=MISSING_REFRESH_TOKEN["message"], code=MISSING_REFRESH_TOKEN["code"])

        serializer = TokenRefreshSerializer(data={"refresh": refresh_token})

        try:
            serializer.is_valid(raise_exception=True)
            new_access_token = serializer.validated_data["access"]
            new_csrf_token = generate_csrf_token(request)

            response = success_response(
                message=TOKEN_REFRESH_RESPONSE["message"],
                data={"access_token": new_access_token, "csrf_token": new_csrf_token},
                code=status.HTTP_200_OK,
            )
            logger.info(f"Token refreshed successfully for user {request.user.email}")
            return response
        except ValidationError as e:
            logger.warning(f"Token refresh failed due to validation error: {e.detail}", exc_info=True)
            return error_response(message=INVALID_REFRESH_TOKEN["message"], code=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            logger.error(f"Unexpected error during token refresh: {e}", exc_info=True)
            raise ServerError() from e


class TokenInfoAPIView(APIView):
    """
    토큰 정보 확인 API.

    현재 로그인한 사용자의 토큰 정보를 반환합니다.
    """

    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    @swagger_auto_schema(
        tags=["유저/인증"],
        operation_summary="토큰 정보 확인",
        operation_description="현재 로그인한 사용자의 유효한 액세스 토큰 정보를 확인합니다.",
        responses={
            200: UserSerializer,
            401: openapi.Response(
                description="JWT 인증 실패",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "code": openapi.Schema(type=openapi.TYPE_INTEGER, example=401),
                        "message": openapi.Schema(type=openapi.TYPE_STRING, example="인증 정보가 없습니다."),
                        "data": None,
                    },
                ),
            ),
        },
    )
    def get(self, request):
        # 사용자 인스턴스를 직렬화하여 반환
        serializer = UserSerializer(request.user)
        logger.info(f"Token info retrieved successfully for user {request.user.email}")
        return success_response(
            message=PROFILE_RETRIEVE_RESPONSE["message"],
            data=serializer.data,
            code=status.HTTP_200_OK,
        )


class UserBulkApproveView(APIView):
    permission_classes = [permissions.IsAdminUser]
    authentication_classes = [JWTAuthentication]

    @swagger_auto_schema(
        tags=["관리자/유저"],
        operation_summary="사용자 계정 일괄 승인 (관리자 전용)",
        operation_description="관리자가 여러 사용자의 계정을 동시에 활성화합니다. 이메일 인증이 완료되었지만 아직 승인되지 않은 사용자들을 대상으로 합니다.",
        request_body=UserBulkApproveSerializer,
        responses={
            200: openapi.Response(
                description="선택된 사용자 계정이 성공적으로 활성화되었습니다.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="선택된 사용자 계정이 성공적으로 활성화되었습니다.",
                        ),
                        "approved_count": openapi.Schema(type=openapi.TYPE_INTEGER, example=5),
                    },
                ),
            ),
            400: openapi.Response(
                description="잘못된 요청",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "error": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="잘못된 사용자 ID 목록입니다.",
                        ),
                    },
                ),
            ),
            403: "관리자 권한이 없습니다.",
        },
    )
    def post(self, request):
        serializer = UserBulkApproveSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            user_ids = serializer.validated_data["user_ids"]
            approved_count = 0
            for user_id in user_ids:
                try:
                    user = User.objects.get(id=user_id)
                    if not user.is_active:
                        user.is_active = True
                        user.save()
                        approved_count += 1
                        logger.info(f"User {user.email} (ID: {user.id}) approved by admin.")
                except User.DoesNotExist as e:
                    logger.warning(f"User with ID {user_id} not found during bulk approval.", exc_info=True)
                    # 특정 사용자 ID에 대한 오류는 무시하고 다음으로 진행
                except Exception as e:
                    logger.error(f"Error approving user {user_id}: {e}", exc_info=True)
                    raise ServerError() from e

            return success_response(
                message="선택된 사용자 계정이 성공적으로 활성화되었습니다.",
                data={"approved_count": approved_count},
            )
        except ValidationError as e:
            logger.warning(f"User bulk approval failed due to validation error: {e.detail}", exc_info=True)
            return error_response(message="잘못된 사용자 ID 목록입니다.", data=e.detail)
        except Exception as e:
            logger.error(f"Unexpected error during user bulk approval: {e}", exc_info=True)
            raise ServerError() from e


class EmailVerificationView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="이메일 인증",
        request_body=EmailVerificationSerializer,
        responses={
            200: "이메일 인증 성공",
            400: "잘못된 토큰",
            404: "사용자를 찾을 수 없음",
            410: "만료된 토큰",
        },
    )
    def post(self, request):
        serializer = EmailVerificationSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            email = serializer.validated_data["email"]
            token = serializer.validated_data["token"]

            signer = TimestampSigner()
            signed_email = signing.loads(token, max_age=timedelta(minutes=settings.EMAIL_VERIFICATION_TIMEOUT_MINUTES))
            if signer.unsign(signed_email) != email:
                logger.warning(f"Email verification failed: Email mismatch for token {token}")
                return error_response(message=INVALID_SIGNATURE["message"], code=INVALID_SIGNATURE["code"])

            user = get_object_or_404(User, email=email)

            if user.is_email_verified:
                logger.info(f"Email verification failed: Email already verified for user {email}")
                return error_response(message=VERIFY_EMAIL_ALREADY_VERIFIED["message"])

            user.is_email_verified = True
            user.is_active = True
            user.save()
            logger.info(f"Email verified successfully for user {email}")
            return success_response(message=VERIFY_EMAIL_SUCCESS["message"])
        except SignatureExpired as e:
            logger.warning(f"Email verification failed: Signature expired. Token: {token}", exc_info=True)
            return error_response(message=SIGNATURE_EXPIRED["message"], code=SIGNATURE_EXPIRED["code"])
        except signing.BadSignature as e:
            logger.warning(f"Email verification failed: Invalid signature. Token: {token}", exc_info=True)
            return error_response(message=INVALID_SIGNATURE["message"], code=INVALID_SIGNATURE["code"])
        except User.DoesNotExist as e:
            logger.warning(f"Email verification failed: User not found for email {email}", exc_info=True)
            raise UserNotFoundError() from e
        except Exception as e:
            logger.error(f"Unexpected error during email verification POST: {e}", exc_info=True)
            raise ServerError() from e


class ResendVerificationEmailView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="이메일 인증이 완료되지 않은 사용자에게 인증 이메일을 재전송합니다.",
        request_body=ResendVerificationEmailSerializer,
        responses={
            200: "인증 이메일 전송 성공",
            400: "잘못된 요청",
            404: "사용자를 찾을 수 없음",
            429: "너무 많은 요청",
        },
    )
    def post(self, request):
        serializer = ResendVerificationEmailSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            email = serializer.validated_data["email"]
            user = get_object_or_404(User, email=email)

            if user.is_email_verified:
                logger.info(f"Resend verification email failed: Email already verified for user {email}")
                return error_response(message=VERIFY_EMAIL_ALREADY_VERIFIED["message"])

            signer = TimestampSigner()
            signed_email = signer.sign(user.email)
            signed_code = signing.dumps(signed_email)

            verify_url = f"{request.scheme}://{request.get_host()}/api/users/verify/email?code={signed_code}"

            subject = "[WiStar] 이메일 인증을 완료해주세요."
            message = f"아래 링크를 클릭해 인증을 완료해주세요.\n\n{verify_url}"
            send_email(subject, message, user.email)

            logger.info(f"Verification email resent successfully to {user.email}")
            return success_response(message="인증 이메일 전송에 성공했습니다.")
        except User.DoesNotExist as e:
            logger.warning(f"Resend verification email failed: User not found for email {email}", exc_info=True)
            raise UserNotFoundError() from e
        except SMTPException as e:
            logger.error(
                f"Email sending failed during resend verification for user {user.email}: {e}",
                exc_info=True,
            )
            raise CustomAPIException(EMAIL_SEND_FAILED) from e
        except Exception as e:
            logger.error(f"Unexpected error during password reset: {e}", exc_info=True)
            raise ServerError() from e


class UserPasswordChangeAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PasswordChangeSerializer

    @swagger_auto_schema(
        tags=["유저"],
        operation_summary="비밀번호 변경",
        operation_description="현재 로그인한 사용자의 비밀번호를 변경합니다.",
        request_body=PasswordChangeSerializer,
        responses={
            200: openapi.Response(
                description="비밀번호 변경 성공",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "code": openapi.Schema(type=openapi.TYPE_INTEGER, example=PASSWORD_CHANGED["code"]),
                        "message": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example=PASSWORD_CHANGED["message"],
                        ),
                        "data": None,
                    },
                ),
            ),
            400: openapi.Response(
                description="잘못된 요청",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "code": openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            example=INVALID_PROFILE_UPDATE["code"],
                        ),
                        "message": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example=INVALID_PROFILE_UPDATE["message"],
                        ),
                        "data": None,
                    },
                ),
            ),
            401: openapi.Response(
                description="인증되지 않은 사용자",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "code": openapi.Schema(type=openapi.TYPE_INTEGER, example=UNAUTHORIZED["code"]),
                        "message": openapi.Schema(type=openapi.TYPE_STRING, example=UNAUTHORIZED["message"]),
                        "data": None,
                    },
                ),
            ),
        },
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        try:
            serializer.is_valid(raise_exception=True)
            serializer.save()
            logger.info(f"Password changed successfully for user {request.user.email}")
            return success_response(message=PASSWORD_CHANGED["message"])
        except ValidationError as e:
            logger.warning(
                f"Password change failed due to validation error for user {request.user.email}: {e.detail}",
                exc_info=True,
            )
            return error_response(message=PASSWORD_NOT_MATCH["message"])
        except Exception as e:
            logger.error(f"Unexpected error during password change for user {request.user.email}: {e}", exc_info=True)
            raise ServerError() from e


class PasswordResetView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="비밀번호 재설정 이메일 요청",
        operation_description="등록된 이메일로 비밀번호 재설정 링크를 전송합니다.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={"email": openapi.Schema(type=openapi.TYPE_STRING, format="email")},
        ),
        responses={
            200: "비밀번호 재설정 이메일 전송 성공",
            400: "잘못된 이메일 형식",
            404: "사용자를 찾을 수 없음",
        },
    )
    def post(self, request):
        serializer = ResendVerificationEmailSerializer(data=request.data)  # 이메일 유효성 검사만 위해 재활용
        try:
            serializer.is_valid(raise_exception=True)
            email = serializer.validated_data["email"]
            user = get_object_or_404(User, email=email)

            signer = TimestampSigner()
            signed_token = signer.sign(str(user.pk))
            reset_url = f"{request.scheme}://{request.get_host()}/reset-password?uid={user.pk}&token={signed_token}"

            subject = "[WiStar] 비밀번호 재설정 링크입니다."
            message = f"다음 링크를 사용하여 비밀번호를 재설정하세요:\n\n{reset_url}"
            send_email(subject, message, user.email)

            logger.info(f"Password reset email sent to {user.email}")
            return success_response(message="비밀번호 재설정 이메일이 전송되었습니다.")
        except User.DoesNotExist as e:
            logger.warning(f"Password reset request failed: User not found for email {email}", exc_info=True)
            raise UserNotFoundError() from e
        except SMTPException as e:
            logger.error(
                f"Email sending failed during password reset for user {user.email}: {e}",
                exc_info=True,
            )
            raise CustomAPIException(EMAIL_SEND_FAILED) from e
        except Exception as e:
            logger.error(f"Unexpected error during password reset: {e}", exc_info=True)
            raise ServerError() from e


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="비밀번호 재설정 확인",
        operation_description="이메일로 전송된 토큰과 새 비밀번호를 사용하여 비밀번호를 재설정합니다.",
        request_body=PasswordResetConfirmSerializer,
        responses={
            200: "비밀번호 재설정 성공",
            400: "잘못된 요청 (예: 토큰 만료, 유효하지 않은 비밀번호)",
            404: "사용자를 찾을 수 없음",
        },
    )
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            uid = serializer.validated_data["uid"]
            token = serializer.validated_data["token"]
            new_password = serializer.validated_data["new_password"]

            user = get_object_or_404(User, pk=uid)

            signer = TimestampSigner()
            if signer.unsign(token) != str(user.pk):
                logger.warning(f"Password reset confirm failed: Invalid token for user ID {uid}")
                return error_response(message=INVALID_SIGNATURE["message"], code=INVALID_SIGNATURE["code"])

            user.set_password(new_password)
            user.save()
            logger.info(f"Password reset successfully for user {user.email}")
            return success_response(message="비밀번호가 성공적으로 재설정되었습니다.")
        except SignatureExpired as e:
            logger.warning(f"Password reset confirm failed: Token expired for user ID {uid}", exc_info=True)
            return error_response(message=SIGNATURE_EXPIRED["message"], code=SIGNATURE_EXPIRED["code"])
        except signing.BadSignature as e:
            logger.warning(f"Password reset confirm failed: Invalid signature for user ID {uid}", exc_info=True)
            return error_response(message=INVALID_SIGNATURE["message"], code=INVALID_SIGNATURE["code"])
        except User.DoesNotExist as e:
            logger.warning(f"Password reset confirm failed: User not found for ID {uid}", exc_info=True)
            raise UserNotFoundError() from e
        except Exception as e:
            logger.error(f"Unexpected error during password reset confirmation: {e}", exc_info=True)
            raise ServerError() from e


class UserListView(APIView):
    """
    사용자 목록 조회 API.

    관리자만 접근 가능한 사용자 목록 조회 API입니다.
    """

    permission_classes = [permissions.IsAdminUser]
    authentication_classes = [JWTAuthentication]

    @swagger_auto_schema(
        tags=["관리자/유저"],
        operation_summary="사용자 목록 조회",
        operation_description="관리자가 모든 사용자의 목록을 조회합니다.",
        responses={
            200: UserSerializer(many=True),
            401: "인증되지 않은 사용자",
            403: "권한이 없는 사용자",
        },
    )
    def get(self, request):
        users = User.objects.all().order_by("-date_joined")
        serializer = UserSerializer(users, many=True)
        logger.info(f"Admin {request.user.email} retrieved user list.")
        return success_response(
            message="사용자 목록 조회에 성공했습니다.",
            data=serializer.data,
        )


class UserProfileView(APIView):
    """
    사용자 프로필 API.

    현재 로그인한 사용자의 프로필을 조회하고 수정할 수 있는 API입니다.
    """

    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    @swagger_auto_schema(
        tags=["유저"],
        operation_summary="프로필 조회",
        operation_description="현재 로그인한 사용자의 프로필을 조회합니다.",
        responses={
            200: UserSerializer,
            401: "인증되지 않은 사용자",
        },
    )
    def get(self, request):
        serializer = UserSerializer(request.user)
        logger.info(f"User {request.user.email} retrieved profile.")
        return success_response(
            message=PROFILE_RETRIEVE_RESPONSE["message"],
            data=serializer.data,
            code=status.HTTP_200_OK,
        )

    @swagger_auto_schema(
        tags=["유저"],
        operation_summary="프로필 수정",
        operation_description="현재 로그인한 사용자의 프로필을 수정합니다.",
        request_body=ProfileUpdateSerializer,
        responses={
            200: UserSerializer,
            400: "잘못된 요청",
            401: "인증되지 않은 사용자",
        },
    )
    def put(self, request):
        serializer = ProfileUpdateSerializer(request.user, data=request.data, partial=True)
        try:
            serializer.is_valid(raise_exception=True)
            serializer.save()
            logger.info(f"User {request.user.email} updated profile successfully.")
            return success_response(
                message=PROFILE_UPDATE_RESPONSE["message"],
                data=serializer.data,
                code=status.HTTP_200_OK,
            )
        except IntegrityError as e:
            if "nickname" in str(e):
                logger.warning(
                    f"Profile update failed due to duplicate nickname for user {request.user.email}: {serializer.validated_data.get('nickname')}",
                )
                raise DuplicateNicknameError() from e
            else:
                logger.error(
                    f"Database integrity error during profile update for user {request.user.email}: {e}", exc_info=True
                )
                raise ServerError() from e
        except ValidationError as e:
            logger.warning(
                f"Profile update failed due to validation error for user {request.user.email}: {e.detail}",
                exc_info=True,
            )
            return error_response(message=INVALID_PROFILE_UPDATE["message"], data=e.detail)
        except Exception as e:
            logger.error(f"Unexpected error during profile update for user {request.user.email}: {e}", exc_info=True)
            raise ServerError() from e
