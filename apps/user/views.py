import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core import signing
from django.core.cache import cache
from django.core.exceptions import SMTPException
from django.core.signing import SignatureExpired, TimestampSigner
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import (
    CreateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.serializers import (
    TokenRefreshSerializer,
)
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.user.models import User
from apps.user.serializers import (
    EmailVerificationSerializer,
    LogoutSerializer,
    PasswordChangeSerializer,
    PasswordResetConfirmSerializer,
    ProfileSerializer,
    ProfileUpdateSerializer,
    RegisterSerializer,
    ResendVerificationEmailSerializer,
    UserBulkApproveSerializer,
)
from apps.user.throttles import LoginAttemptThrottle
from utils.cache_helpers import invalidate_user_cache
from utils.csrf import generate_csrf_token, validate_csrf_token
from utils.email import send_email
from utils.responses.common import error_response, success_response
from utils.responses.user import (
    CSRF_INVALID_TOKEN,
    EMAIL_SEND_FAILED,
    INVALID_INPUT,
    INVALID_PASSWORD,
    INVALID_REFRESH_TOKEN,
    INVALID_SIGNATURE,
    LOGIN_FAILED,
    LOGIN_SUCCESS,
    LOGOUT_SUCCESS,
    MISSING_REFRESH_TOKEN,
    PASSWORD_CHANGED,
    PROFILE_RETRIEVE_RESPONSE,
    PROFILE_UPDATE_RESPONSE,
    SIGNATURE_EXPIRED,
    SIGNUP_PASSWORD_MISMATCH,
    SIGNUP_SUCCESS,
    TOKEN_REFRESH_RESPONSE,
    UNAUTHORIZED,
    VERIFY_EMAIL_ALREADY_VERIFIED,
    VERIFY_EMAIL_SUCCESS,
    WEAK_PASSWORD,
)
from utils.responses.user import SERVER_ERROR as SERVER_ERROR_RESPONSE

from .exceptions import (
    CustomAPIException,
    DuplicateEmailError,
    DuplicateNicknameError,
    EmailAlreadyVerifiedError,
    ServerError,
    UserNotFoundError,
)

logger = logging.getLogger("apps")

User = get_user_model()


# 회원 가입
class RegisterView(CreateAPIView):
    """회원가입 API.

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
    def post(self, request, *args, **kwargs):  # 스웨거 데코레이터 사용하기 위해 오버라이드(원래 동작과 동일)
        return self.create(request, *args, **kwargs)  # CreateAPIView가 내부적으로 사용하는 create 호출

    def create(self, request, *args, **kwargs):
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
            return Response(custom_response, status=status.HTTP_201_CREATED)
        except IntegrityError as e:
            if "email" in str(e):
                logger.warning(f"Registration failed due to duplicate email: {serializer.validated_data.get('email')}")
                raise DuplicateEmailError()
            elif "nickname" in str(e):
                logger.warning(
                    f"Registration failed due to duplicate nickname: {serializer.validated_data.get('nickname')}"
                )
                raise DuplicateNicknameError()
            else:
                logger.error(f"Database integrity error during registration: {e}", exc_info=True)
                raise ServerError()
        except SMTPException as e:
            logger.error(
                f"Email sending failed during registration for user {user.email}: {e}",
                exc_info=True,
            )
            raise CustomAPIException(EMAIL_SEND_FAILED)
        except Exception as e:
            logger.error(f"Unexpected error during user registration: {e}", exc_info=True)
            raise ServerError()


# 이메일 인증
class VerifyEmailView(APIView):
    """이메일 인증 API.

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
        code = request.GET.get("code")
        if not code:
            raise CustomAPIException(INVALID_SIGNATURE)

        try:
            signed_email = signing.loads(code, max_age=settings.EMAIL_VERIFICATION_TIMEOUT)
            user = get_object_or_404(User, email=signed_email)

            if user.is_email_verified:
                raise EmailAlreadyVerifiedError()

            user.is_email_verified = True
            user.is_active = True
            user.save()

            logger.info(f"Email verified successfully for user: {user.email}")
            return Response(VERIFY_EMAIL_SUCCESS)
        except signing.BadSignature:
            raise CustomAPIException(INVALID_SIGNATURE)
        except SignatureExpired:
            raise CustomAPIException(SIGNATURE_EXPIRED)
        except Exception as e:
            logger.error(f"Unexpected error during email verification: {e}", exc_info=True)
            raise ServerError()


# JWT 로그인
class CustomTokenObtainPairView(TokenObtainPairView):
    """JWT 로그인 API.

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
        # CustomTokenObtainPairSerializer를 사용하여 토큰 발급 및 응답 생성
        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:
            # 사용자 정보 가져오기
            user = User.objects.get(email=request.data["email"])
            user.last_login = timezone.now()
            user.save()

            # CSRF 토큰 생성
            csrf_token = generate_csrf_token()

            # 응답 데이터 구성
            response_data = {
                "code": LOGIN_SUCCESS["code"],
                "message": LOGIN_SUCCESS["message"],
                "data": {
                    "access_token": response.data["access"],
                    "csrf_token": csrf_token,
                },
            }

            # 리프레시 토큰을 HttpOnly 쿠키로 설정
            response = Response(response_data)
            response.set_cookie(
                key="refresh_token",
                value=response.data["refresh"],
                httponly=True,
                secure=settings.COOKIE_SECURE,
                samesite=settings.COOKIE_SAMESITE,
                path="/api/users/token",
                max_age=settings.REFRESH_TOKEN_LIFETIME.total_seconds(),
            )

            # 로그인 성공 시 실패 시도 횟수 초기화
            ident = self.get_ident(request)
            cache.delete(f"login_failed_attempts_{ident}")
            cache.delete(f"login_last_failed_attempt_time_{ident}")

            logger.info(f"User logged in successfully: {user.email}")
            return response

        # 로그인 실패 시 실패 시도 횟수 증가
        ident = self.get_ident(request)
        failed_attempts = cache.get(f"login_failed_attempts_{ident}", 0) + 1
        cache.set(f"login_failed_attempts_{ident}", failed_attempts)
        cache.set(f"login_last_failed_attempt_time_{ident}", timezone.now())

        logger.warning(f"Login failed for email: {request.data.get('email')}")
        return Response(LOGIN_FAILED, status=status.HTTP_401_UNAUTHORIZED)


# 로그아웃
class LogoutAPIView(APIView):
    """JWT 로그아웃 API.

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
    def post(self, request, *args, **kwargs):
        # 쿠키에서 Refresh Token 가져오기
        refresh_token = request.COOKIES.get("refresh_token")
        if not refresh_token:
            logger.warning("Logout failed: No refresh token in cookies")
            raise CustomAPIException(MISSING_REFRESH_TOKEN)

        # Refresh Token 블랙리스트에 추가
        serializer = LogoutSerializer(data={"refresh_token": refresh_token})
        try:
            serializer.is_valid(raise_exception=True)
            serializer.save()
        except Exception as e:
            logger.error(f"Error during logout: {e}", exc_info=True)
            raise CustomAPIException(INVALID_REFRESH_TOKEN)

        # 쿠키에서 Refresh Token 삭제
        response = Response(LOGOUT_SUCCESS)
        response.delete_cookie(
            key="refresh_token",
            path="/api/users/token",
            samesite=settings.COOKIE_SAMESITE,
            secure=settings.COOKIE_SECURE,
        )

        logger.info(f"User logged out successfully: {request.user.email}")
        return response


# 토큰 재발급
class CustomTokenRefreshView(APIView):
    """JWT 토큰 갱신 API.

    HttpOnly 쿠키에 저장된 리프레시 토큰을 사용하여 새로운 액세스 토큰을 발급합니다.
    """

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
    def post(self, request, *args, **kwargs):
        # CSRF 토큰 검증
        csrf_token = request.headers.get("X-CSRFToken")
        if not csrf_token or not validate_csrf_token(csrf_token):
            logger.warning("Token refresh failed: Invalid CSRF token")
            raise CustomAPIException(CSRF_INVALID_TOKEN)

        # 쿠키에서 Refresh Token 가져오기
        refresh_token = request.COOKIES.get("refresh_token")
        if not refresh_token:
            logger.warning("Token refresh failed: No refresh token in cookies")
            raise CustomAPIException(MISSING_REFRESH_TOKEN)

        # Refresh Token으로 새로운 Access Token 발급
        serializer = TokenRefreshSerializer(data={"refresh": refresh_token})
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            logger.error(f"Token refresh failed: {e}", exc_info=True)
            raise CustomAPIException(INVALID_REFRESH_TOKEN)

        # 새로운 CSRF 토큰 생성
        new_csrf_token = generate_csrf_token()

        # 응답 데이터 구성
        response_data = {
            "code": TOKEN_REFRESH_RESPONSE["code"],
            "message": TOKEN_REFRESH_RESPONSE["message"],
            "data": {
                "access_token": serializer.validated_data["access"],
                "csrf_token": new_csrf_token,
            },
        }

        logger.info("Token refreshed successfully")
        return Response(response_data)


# 토큰 정보 확인
# https://jwt.io/


class TokenInfoAPIView(APIView):
    """토큰 정보 확인 API.

    현재 로그인한 사용자의 토큰 정보를 반환합니다.
    """

    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    @swagger_auto_schema(
        tags=["유저/인증"],
        operation_summary="토큰 정보 확인",
        operation_description="현재 로그인한 사용자의 유효한 액세스 토큰 정보를 확인합니다.",
        responses={
            200: openapi.Response(
                description="토큰 정보 확인 성공",
                schema=ProfileSerializer,
            ),
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
        user = request.user
        serializer = ProfileSerializer(user)
        logger.info(f"Token info retrieved for user: {user.email}")
        return success_response(data=serializer.data, message="토큰 정보 확인 성공")


# 유저 수전 승인 (관리자 전용)
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
    def post(self, request, *args, **kwargs):
        serializer = UserBulkApproveSerializer(data=request.data)
        if serializer.is_valid():
            user_ids = serializer.validated_data["user_ids"]
            approved_count = 0

            for user_id in user_ids:
                try:
                    user = User.objects.get(id=user_id, is_active=False, is_email_verified=True)
                    user.is_active = True
                    user.save()
                    approved_count += 1
                    logger.info(f"User {user.email} approved by admin {request.user.email}")
                except User.DoesNotExist:
                    continue

            return success_response(
                data={"approved_count": approved_count},
                message="선택된 사용자 계정이 성공적으로 활성화되었습니다.",
            )
        return error_response(INVALID_INPUT)


# 유저 프로필 조회 및 업데이트
class UserProfileView(RetrieveUpdateDestroyAPIView):
    """사용자 프로필 조회, 수정, 삭제(비활성화) API.

    - GET: 현재 로그인한 사용자의 프로필 정보를 조회합니다.
    - PATCH: 현재 로그인한 사용자의 프로필 정보를 수정합니다.
    - DELETE: 현재 로그인한 사용자의 계정을 비활성화합니다.
    """

    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    @swagger_auto_schema(
        tags=["유저/프로필"],
        operation_summary="프로필 조회",
        operation_description="현재 로그인한 사용자의 프로필 정보를 조회합니다.",
        responses={
            200: openapi.Response(
                description="프로필 조회 성공",
                schema=ProfileSerializer,
            ),
            401: openapi.Response(
                description="인증되지 않은 사용자",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "code": openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            example=UNAUTHORIZED["code"],
                        ),
                        "message": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example=UNAUTHORIZED["message"],
                        ),
                        "data": None,
                    },
                ),
            ),
        },
    )
    def get(self, request, *args, **kwargs):
        """사용자 프로필 정보를 조회합니다."""
        serializer = self.serializer_class(request.user)
        response_data = {
            "code": PROFILE_RETRIEVE_RESPONSE["code"],
            "message": PROFILE_RETRIEVE_RESPONSE["message"],
            "data": serializer.data,
        }
        return Response(response_data)

    @swagger_auto_schema(
        tags=["유저/프로필"],
        operation_summary="프로필 수정",
        operation_description="현재 로그인한 사용자의 프로필 정보를 수정합니다.",
        request_body=ProfileUpdateSerializer,
        responses={
            200: openapi.Response(
                description="프로필 수정 성공",
                schema=ProfileSerializer,
            ),
            400: openapi.Response(
                description="유효하지 않은 입력",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "code": openapi.Schema(type=openapi.TYPE_INTEGER, example=400),
                        "message": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="닉네임은 필수 항목입니다.",
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
                        "code": openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            example=UNAUTHORIZED["code"],
                        ),
                        "message": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example=UNAUTHORIZED["message"],
                        ),
                        "data": None,
                    },
                ),
            ),
        },
    )
    def patch(self, request, *args, **kwargs):
        """사용자 프로필 정보를 수정합니다."""
        serializer = self.serializer_class(request.user, data=request.data, partial=True)
        if not serializer.is_valid():
            logger.warning(f"Profile update failed: {serializer.errors}")
            raise CustomAPIException(INVALID_INPUT)

        serializer.save()
        response_data = {
            "code": PROFILE_UPDATE_RESPONSE["code"],
            "message": PROFILE_UPDATE_RESPONSE["message"],
            "data": serializer.data,
        }
        logger.info(f"Profile updated successfully for user: {request.user.email}")
        return Response(response_data)

    @swagger_auto_schema(
        tags=["유저/프로필"],
        operation_summary="계정 비활성화",
        operation_description="현재 로그인한 사용자의 계정을 비활성화합니다. 계정 비활성화는 탈퇴를 의미하며, 비활성화된 계정은 로그인할 수 없습니다.",
        responses={
            200: openapi.Response(
                description="계정 비활성화 성공",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="계정이 비활성화되었습니다.",
                        ),
                        "status": openapi.Schema(type=openapi.TYPE_STRING, example="success"),
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
    def delete(self, request, *args, **kwargs):
        try:
            response = super().delete(request, *args, **kwargs)
            invalidate_user_cache(request.user.id)  # 통합된 캐시 무효화 함수 사용
            logger.info(f"User account deactivated successfully and cache invalidated for user: {request.user.email}")
            return success_response(data=None, message="계정이 비활성화되었습니다.")
        except Exception as e:
            logger.error(
                f"User account deactivation failed for user {request.user.email}: {e}",
                exc_info=True,
            )
            return error_response(message="계정 비활성화 실패", code=500)

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return ProfileUpdateSerializer
        return ProfileSerializer

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"message": "계정이 비활성화되었습니다.", "status": "success"},
            status=status.HTTP_200_OK,
        )


# 이메일 인증 토큰 생성/확인
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
        if not serializer.is_valid():
            return error_response(INVALID_INPUT)

        try:
            code = serializer.validated_data["code"]
            signed_email = signing.loads(code)
            email = TimestampSigner().unsign(signed_email, max_age=settings.EMAIL_VERIFICATION_TIMEOUT)
            user = User.objects.get(email=email)

            if user.is_email_verified:
                return error_response(VERIFY_EMAIL_ALREADY_VERIFIED)

            user.is_email_verified = True
            user.save()
            logger.info(f"Email verified for user: {user.email}")
            return success_response(message=VERIFY_EMAIL_SUCCESS["message"])

        except signing.BadSignature:
            logger.warning(f"Invalid verification code attempted: {code}")
            return error_response(INVALID_SIGNATURE)
        except SignatureExpired:
            logger.warning(f"Expired verification code attempted: {code}")
            return error_response(SIGNATURE_EXPIRED)
        except User.DoesNotExist:
            logger.warning(f"Verification attempted for non-existent user with email: {email}")
            return error_response(UserNotFoundError())
        except Exception as e:
            logger.error(f"Unexpected error during email verification: {e}", exc_info=True)
            return error_response(SERVER_ERROR_RESPONSE)


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
        if not serializer.is_valid():
            return error_response(INVALID_INPUT)

        try:
            email = serializer.validated_data["email"]
            user = User.objects.get(email=email)

            if user.is_email_verified:
                return error_response(VERIFY_EMAIL_ALREADY_VERIFIED)

            signer = TimestampSigner()
            signed_email = signer.sign(user.email)
            signed_code = signing.dumps(signed_email)

            verify_url = f"{request.scheme}://{request.get_host()}/api/users/verify/email?code={signed_code}"

            subject = "[WiStar] 이메일 인증을 완료해주세요."
            message = f"아래 링크를 클릭해 인증을 완료해주세요.\n\n{verify_url}"
            send_email(subject, message, user.email)

            logger.info(f"Verification email resent to user: {user.email}")
            return success_response(message="인증 이메일이 재전송되었습니다.")

        except User.DoesNotExist:
            logger.warning(f"Resend verification attempted for non-existent user with email: {email}")
            return error_response(UserNotFoundError())
        except SMTPException as e:
            logger.error(f"Failed to send verification email to {email}: {e}", exc_info=True)
            return error_response(EMAIL_SEND_FAILED)
        except Exception as e:
            logger.error(f"Unexpected error during verification email resend: {e}", exc_info=True)
            return error_response(SERVER_ERROR_RESPONSE)


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
                        "code": openapi.Schema(type=openapi.TYPE_INTEGER, example=INVALID_INPUT["code"]),
                        "message": openapi.Schema(type=openapi.TYPE_STRING, example=INVALID_INPUT["message"]),
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
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return error_response(INVALID_INPUT)

        try:
            user = request.user
            old_password = serializer.validated_data["old_password"]
            new_password = serializer.validated_data["new_password"]

            if not user.check_password(old_password):
                return error_response(INVALID_PASSWORD)

            try:
                validate_password(new_password, user)
            except ValidationError as e:
                return error_response(WEAK_PASSWORD)

            user.set_password(new_password)
            user.save()
            logger.info(f"Password changed for user: {user.email}")
            return success_response(message=PASSWORD_CHANGED["message"])

        except Exception as e:
            logger.error(f"Unexpected error during password change: {e}", exc_info=True)
            return error_response(SERVER_ERROR_RESPONSE)


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
        email = request.data.get("email")
        if not email:
            return error_response(INVALID_INPUT)

        try:
            user = User.objects.get(email=email)
            signer = TimestampSigner()
            signed_email = signer.sign(user.email)
            signed_code = signing.dumps(signed_email)

            reset_url = f"{request.scheme}://{request.get_host()}/api/users/reset-password/confirm?code={signed_code}"

            subject = "[WiStar] 비밀번호 재설정"
            message = f"아래 링크를 클릭해 비밀번호를 재설정해주세요.\n\n{reset_url}"
            send_email(subject, message, user.email)

            logger.info(f"Password reset email sent to user: {user.email}")
            return success_response(message="비밀번호 재설정 이메일이 전송되었습니다.")

        except User.DoesNotExist:
            logger.warning(f"Password reset attempted for non-existent user with email: {email}")
            return error_response(UserNotFoundError())
        except SMTPException as e:
            logger.error(f"Failed to send password reset email to {email}: {e}", exc_info=True)
            return error_response(EMAIL_SEND_FAILED)
        except Exception as e:
            logger.error(f"Unexpected error during password reset request: {e}", exc_info=True)
            return error_response(SERVER_ERROR_RESPONSE)


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
        if not serializer.is_valid():
            return error_response(INVALID_INPUT)

        try:
            code = serializer.validated_data["code"]
            new_password = serializer.validated_data["new_password"]

            signed_email = signing.loads(code)
            email = TimestampSigner().unsign(signed_email, max_age=settings.PASSWORD_RESET_TIMEOUT)
            user = User.objects.get(email=email)

            try:
                validate_password(new_password, user)
            except ValidationError as e:
                return error_response(WEAK_PASSWORD)

            user.set_password(new_password)
            user.save()
            logger.info(f"Password reset completed for user: {user.email}")
            return success_response(message="비밀번호가 성공적으로 재설정되었습니다.")

        except signing.BadSignature:
            logger.warning(f"Invalid password reset code attempted: {code}")
            return error_response(INVALID_SIGNATURE)
        except SignatureExpired:
            logger.warning(f"Expired password reset code attempted: {code}")
            return error_response(SIGNATURE_EXPIRED)
        except User.DoesNotExist:
            logger.warning(f"Password reset attempted for non-existent user with email: {email}")
            return error_response(UserNotFoundError())
        except Exception as e:
            logger.error(
                f"Unexpected error during password reset confirmation: {e}",
                exc_info=True,
            )
            return error_response(SERVER_ERROR_RESPONSE)
