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
    NicknameCheckSerializer,
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
from utils.email import send_email_async
from utils.jwt_serializers import WiStarTokenObtainPairSerializer
from utils.response import (
    CSRF_INVALID_TOKEN,
    DUPLICATE_NICKNAME,
    EMAIL_SEND_FAILED,
    INVALID_REFRESH_TOKEN,
    INVALID_SIGNATURE,
    LOGIN_FAILED,
    LOGIN_SUCCESS,
    LOGOUT_SUCCESS,
    MISSING_REFRESH_TOKEN,
    PASSWORD_CHANGED,
    PROFILE_RETRIEVE_RESPONSE,
    PROFILE_UPDATE_RESPONSE,
    SERVER_ERROR,
    SIGNATURE_EXPIRED,
    SIGNUP_PASSWORD_MISMATCH,
    SIGNUP_SUCCESS,
    TOKEN_REFRESH_RESPONSE,
    UNAUTHORIZED,
    VERIFY_EMAIL_ALREADY_VERIFIED,
    VERIFY_EMAIL_SUCCESS,
    WEAK_PASSWORD,
    BaseResponseMixin,
)

# Local app imports
from .exceptions import (
    INVALID_PROFILE_UPDATE,
    CustomAPIException,
    DuplicateEmailError,
    DuplicateNicknameError,
    ServerError,
    UserNotFoundError,
)

User = get_user_model()


# 회원 가입
class RegisterView(BaseResponseMixin, CreateAPIView):
    logger = logging.getLogger("apps")
    """
    회원가입 API.

    새로운 사용자를 생성하고, 이메일 인증을 위한 이메일을 전송합니다.
    """

    queryset = User.objects.all()  # Model
    serializer_class = RegisterSerializer  # Serializer
    permission_classes = [AllowAny]

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
            # 기존: send_email(subject, message, user.email)
            send_email_async.delay(subject, message, user.email)  # Celery 비동기 발송

            response_data = serializer.data

            if settings.DEBUG:
                response_data["verify_url"] = verify_url

            self.logger.info(f"User registered successfully: {user.email}")
            return self.success(
                message=SIGNUP_SUCCESS["message"],
                data=response_data,
                code=SIGNUP_SUCCESS["code"],
                status=status.HTTP_201_CREATED,
            )
        except IntegrityError as e:
            if "email" in str(e):
                self.logger.warning(
                    f"Registration failed due to duplicate email: {serializer.validated_data.get('email')}"
                )
                raise DuplicateEmailError() from e
            elif "nickname" in str(e):
                self.logger.warning(
                    f"Registration failed due to duplicate nickname: {serializer.validated_data.get('nickname')}",
                )
                raise DuplicateNicknameError() from e
            else:
                self.logger.error(f"Database integrity error during registration: {e}", exc_info=True)
                raise ServerError() from e
        except SMTPException as e:
            self.logger.error(
                f"Email sending failed during registration for user {user.email}: {e}",
                exc_info=True,
            )
            raise CustomAPIException(EMAIL_SEND_FAILED) from e
        except ValidationError as e:
            self.logger.warning(f"Registration failed due to validation error: {e.detail}", exc_info=True)
            return self.error(message="입력값이 올바르지 않습니다.", data=e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            self.logger.error(f"Unexpected error during user registration: {e}", exc_info=True)
            raise ServerError() from e


# 이메일 인증
class VerifyEmailView(BaseResponseMixin, APIView):
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
            self.logger.warning("Email verification failed: Missing code parameter.")
            return self.error(message=INVALID_SIGNATURE["message"])
        signer = TimestampSigner()
        try:
            signed_email = signing.loads(code, max_age=timedelta(minutes=settings.EMAIL_VERIFICATION_TIMEOUT_MINUTES))
            email = signer.unsign(signed_email)
            user = get_object_or_404(User, email=email)
            if user.is_email_verified:
                self.logger.info(f"Email verification failed: Email already verified for user {email}")
                return self.error(message=VERIFY_EMAIL_ALREADY_VERIFIED["message"])
            user.is_email_verified = True
            user.is_active = True
            user.save()
            self.logger.info(f"Email verified successfully for user {email}")
            return self.success(message=VERIFY_EMAIL_SUCCESS["message"])
        except SignatureExpired as e:
            self.logger.warning(f"Email verification failed: Signature expired. Code: {code}", exc_info=True)
            return self.error(message=SIGNATURE_EXPIRED["message"], code=SIGNATURE_EXPIRED["code"])
        except signing.BadSignature as e:
            self.logger.warning(f"Email verification failed: Invalid signature. Code: {code}", exc_info=True)
            return self.error(message=INVALID_SIGNATURE["message"], code=INVALID_SIGNATURE["code"])
        except User.DoesNotExist as e:
            self.logger.warning(f"Email verification failed: User not found for code {code}", exc_info=True)
            raise UserNotFoundError() from e
        except Exception as e:
            self.logger.error(f"Unexpected error during email verification GET: {e}", exc_info=True)
            raise ServerError() from e


class CustomTokenObtainPairView(TokenObtainPairView, BaseResponseMixin):
    """커스텀 토큰 발급 뷰"""

    serializer_class = WiStarTokenObtainPairSerializer
    permission_classes = [AllowAny]
    throttle_classes = [LoginAttemptThrottle]

    @swagger_auto_schema(
        tags=["유저"],
        operation_summary="JWT 로그인",
        operation_description="이메일과 비밀번호를 사용하여 액세스 토큰과 리프레시 토큰을 발급합니다.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["email", "password"],
            properties={
                "email": openapi.Schema(type=openapi.TYPE_STRING, format="email"),
                "password": openapi.Schema(type=openapi.TYPE_STRING, format="password"),
            },
        ),
        responses={
            200: openapi.Response(
                description="로그인 성공",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "code": openapi.Schema(type=openapi.TYPE_INTEGER, example=200),
                        "message": openapi.Schema(type=openapi.TYPE_STRING, example="로그인에 성공했습니다."),
                        "data": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "access_token": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                                ),
                                "refresh_token": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                                ),
                            },
                        ),
                    },
                ),
            ),
            401: openapi.Response(
                description="로그인 실패",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "code": openapi.Schema(type=openapi.TYPE_INTEGER, example=401),
                        "message": openapi.Schema(type=openapi.TYPE_STRING, example="로그인에 실패했습니다."),
                        "data": openapi.Schema(type=openapi.TYPE_OBJECT, example=None),
                    },
                ),
            ),
        },
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            user = serializer.user
            self.logger.info(f"Authenticated user: {user.email}")
            if not user.is_active:
                self.logger.warning(f"Login failed: Inactive user {user.email}")
                return self.error(
                    message="지정된 자격 증명에 해당하는 활성화된 사용자를 찾을 수 없습니다",
                    code=status.HTTP_401_UNAUTHORIZED,
                )
            tokens = serializer.validated_data
            csrf_token = generate_csrf_token()
            response = self.success(
                message=LOGIN_SUCCESS["message"],
                data={
                    "access_token": tokens["access"],
                    "refresh_token": tokens["refresh"],
                    "csrf_token": csrf_token,
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "nickname": user.nickname,
                        "is_staff": user.is_staff,
                    },
                },
            )
            # refresh_token을 HttpOnly 쿠키에 저장
            response.set_cookie(
                key=settings.SIMPLE_JWT["REFRESH_TOKEN_NAME"],
                value=tokens["refresh"],
                httponly=True,
                secure=False,  # 운영 환경에서는 True로
                samesite="Lax",
                max_age=60 * 60 * 24 * 7,  # 7일
                path="/",
            )
            return response
        except Exception as e:
            self.logger.error(f"Login error: {e}", exc_info=True)
            error_message = LOGIN_FAILED["message"]
            if hasattr(e, "detail"):
                if isinstance(e.detail, dict):
                    error_message = e.detail.get("detail", LOGIN_FAILED["message"])
                elif isinstance(e.detail, list) and len(e.detail) > 0:
                    error_message = str(e.detail[0])
                else:
                    error_message = str(e.detail)
            return self.error(message=error_message, code=status.HTTP_401_UNAUTHORIZED)


class LogoutAPIView(BaseResponseMixin, APIView):
    """
    JWT 로그아웃 API.

    리프레시 토큰을 블랙리스트에 추가하고, HttpOnly 쿠키에서 리프레시 토큰을 삭제합니다.
    """

    permission_classes = [AllowAny]
    logger = logging.getLogger("apps")

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
            self.logger.warning("Logout failed: Refresh token not found in cookies.")
            response = self.success(message=LOGOUT_SUCCESS["message"])
            response.delete_cookie(settings.SIMPLE_JWT["REFRESH_TOKEN_NAME"])
            return response
        serializer = LogoutSerializer(data={"refresh_token": refresh_token})
        try:
            serializer.is_valid(raise_exception=True)
            serializer.save()
        except Exception as e:
            self.logger.warning(f"Logout: refresh_token invalid or already blacklisted: {e}")
            # 무시하고 계속 진행
        response = self.success(message=LOGOUT_SUCCESS["message"])
        response.delete_cookie(settings.SIMPLE_JWT["REFRESH_TOKEN_NAME"])  # HttpOnly 쿠키 삭제
        if hasattr(request.user, "email"):
            self.logger.info(f"User {request.user.email} logged out successfully.")
        else:
            self.logger.info("User (anonymous) logged out successfully.")
        return response


class CustomTokenRefreshView(APIView):
    permission_classes = [AllowAny]

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
        if not validate_csrf_token(csrf_token_header):
            if hasattr(request.user, "email"):
                self.logger.warning(f"Token refresh failed: Invalid CSRF token for user {request.user.email}")
            else:
                self.logger.warning("Token refresh failed: Invalid CSRF token for anonymous user")
            return self.error(message=CSRF_INVALID_TOKEN["message"], code=CSRF_INVALID_TOKEN["code"])

        # 리프레시 토큰 추출
        refresh_token = request.COOKIES.get(settings.SIMPLE_JWT["REFRESH_TOKEN_NAME"])
        if not refresh_token:
            self.logger.warning("Token refresh failed: Missing refresh token in cookies.")
            return self.error(message=MISSING_REFRESH_TOKEN["message"], code=MISSING_REFRESH_TOKEN["code"])

        serializer = TokenRefreshSerializer(data={"refresh": refresh_token})

        try:
            serializer.is_valid(raise_exception=True)
            new_access_token = serializer.validated_data["access"]
            new_csrf_token = generate_csrf_token()

            response = self.success(
                message=TOKEN_REFRESH_RESPONSE["message"],
                data={"access_token": new_access_token, "csrf_token": new_csrf_token},
                code=status.HTTP_200_OK,
            )
            if hasattr(request.user, "email"):
                self.logger.info(f"Token refreshed successfully for user {request.user.email}")
            else:
                self.logger.info("Token refreshed successfully for anonymous user")
            return response
        except ValidationError as e:
            self.logger.warning(f"Token refresh failed due to validation error: {e.detail}", exc_info=True)
            return self.error(message=INVALID_REFRESH_TOKEN["message"], code=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            self.logger.error(f"Unexpected error during token refresh: {e}", exc_info=True)
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
        self.logger.info(f"Token info retrieved successfully for user {request.user.email}")
        return self.success(
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
                        self.logger.info(f"User {user.email} (ID: {user.id}) approved by admin.")
                except User.DoesNotExist as e:
                    self.logger.warning(f"User with ID {user_id} not found during bulk approval.", exc_info=True)
                    # 특정 사용자 ID에 대한 오류는 무시하고 다음으로 진행
                except Exception as e:
                    self.logger.error(f"Error approving user {user_id}: {e}", exc_info=True)
                    raise ServerError() from e

            return self.success(
                message="선택된 사용자 계정이 성공적으로 활성화되었습니다.",
                data={"approved_count": approved_count},
            )
        except ValidationError as e:
            self.logger.warning(f"User bulk approval failed due to validation error: {e.detail}", exc_info=True)
            return self.error(message="잘못된 사용자 ID 목록입니다.", data=e.detail)
        except Exception as e:
            self.logger.error(f"Unexpected error during user bulk approval: {e}", exc_info=True)
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
                self.logger.warning(f"Email verification failed: Email mismatch for token {token}")
                return self.error(message=INVALID_SIGNATURE["message"], code=INVALID_SIGNATURE["code"])

            user = get_object_or_404(User, email=email)

            if user.is_email_verified:
                self.logger.info(f"Email verification failed: Email already verified for user {email}")
                return self.error(message=VERIFY_EMAIL_ALREADY_VERIFIED["message"])

            user.is_email_verified = True
            user.is_active = True
            user.save()
            self.logger.info(f"Email verified successfully for user {email}")
            return self.success(message=VERIFY_EMAIL_SUCCESS["message"])
        except SignatureExpired as e:
            self.logger.warning(f"Email verification failed: Signature expired. Token: {token}", exc_info=True)
            return self.error(message=SIGNATURE_EXPIRED["message"], code=SIGNATURE_EXPIRED["code"])
        except signing.BadSignature as e:
            self.logger.warning(f"Email verification failed: Invalid signature. Token: {token}", exc_info=True)
            return self.error(message=INVALID_SIGNATURE["message"], code=INVALID_SIGNATURE["code"])
        except User.DoesNotExist as e:
            self.logger.warning(f"Email verification failed: User not found for email {email}", exc_info=True)
            raise UserNotFoundError() from e
        except Exception as e:
            self.logger.error(f"Unexpected error during email verification POST: {e}", exc_info=True)
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
                self.logger.info(f"Resend verification email failed: Email already verified for user {email}")
                return self.error(message=VERIFY_EMAIL_ALREADY_VERIFIED["message"])

            signer = TimestampSigner()
            signed_email = signer.sign(user.email)
            signed_code = signing.dumps(signed_email)

            verify_url = f"{request.scheme}://{request.get_host()}/api/users/verify/email?code={signed_code}"

            subject = "[WiStar] 이메일 인증을 완료해주세요."
            message = f"아래 링크를 클릭해 인증을 완료해주세요.\n\n{verify_url}"
            send_email(subject, message, user.email)

            self.logger.info(f"Verification email resent successfully to {user.email}")
            return self.success(message="인증 이메일 전송에 성공했습니다.")
        except User.DoesNotExist as e:
            self.logger.warning(f"Resend verification email failed: User not found for email {email}", exc_info=True)
            raise UserNotFoundError() from e
        except SMTPException as e:
            self.logger.error(
                f"Email sending failed during resend verification for user {user.email}: {e}",
                exc_info=True,
            )
            raise CustomAPIException(EMAIL_SEND_FAILED) from e
        except Exception as e:
            self.logger.error(f"Unexpected error during password reset: {e}", exc_info=True)
            raise ServerError() from e


class UserPasswordChangeAPIView(BaseResponseMixin, APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PasswordChangeSerializer
    logger = logging.getLogger("apps")

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
            self.logger.info(f"Password changed successfully for user {request.user.email}")
            return self.success(
                message=PASSWORD_CHANGED["message"],
                code=PASSWORD_CHANGED["code"],
                status=status.HTTP_200_OK,
            )
        except ValidationError as e:
            self.logger.warning(
                f"Password change failed due to validation error for user {request.user.email}: {e.detail}",
                exc_info=True,
            )
            return self.error(message=SIGNUP_PASSWORD_MISMATCH["message"])
        except Exception as e:
            self.logger.error(
                f"Unexpected error during password change for user {request.user.email}: {e}", exc_info=True
            )
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

            self.logger.info(f"Password reset email sent to {user.email}")
            return self.success(message="비밀번호 재설정 이메일이 전송되었습니다.")
        except User.DoesNotExist as e:
            self.logger.warning(f"Password reset request failed: User not found for email {email}", exc_info=True)
            raise UserNotFoundError() from e
        except SMTPException as e:
            self.logger.error(
                f"Email sending failed during password reset for user {user.email}: {e}",
                exc_info=True,
            )
            raise CustomAPIException(EMAIL_SEND_FAILED) from e
        except Exception as e:
            self.logger.error(f"Unexpected error during password reset: {e}", exc_info=True)
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
                self.logger.warning(f"Password reset confirm failed: Invalid token for user ID {uid}")
                return self.error(message=INVALID_SIGNATURE["message"], code=INVALID_SIGNATURE["code"])

            user.set_password(new_password)
            user.save()
            self.logger.info(f"Password reset successfully for user {user.email}")
            return self.success(message="비밀번호가 성공적으로 재설정되었습니다.")
        except SignatureExpired as e:
            self.logger.warning(f"Password reset confirm failed: Token expired for user ID {uid}", exc_info=True)
            return self.error(message=SIGNATURE_EXPIRED["message"], code=SIGNATURE_EXPIRED["code"])
        except signing.BadSignature as e:
            self.logger.warning(f"Password reset confirm failed: Invalid signature for user ID {uid}", exc_info=True)
            return self.error(message=INVALID_SIGNATURE["message"], code=INVALID_SIGNATURE["code"])
        except User.DoesNotExist as e:
            self.logger.warning(f"Password reset confirm failed: User not found for ID {uid}", exc_info=True)
            raise UserNotFoundError() from e
        except Exception as e:
            self.logger.error(f"Unexpected error during password reset confirmation: {e}", exc_info=True)
            raise ServerError() from e


class UserListView(BaseResponseMixin, APIView):
    """
    사용자 목록 조회 API.

    관리자만 접근 가능한 사용자 목록 조회 API입니다.
    """

    permission_classes = [permissions.IsAdminUser]
    authentication_classes = [JWTAuthentication]
    logger = logging.getLogger("apps")

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
        users = User.objects.all().order_by("-created_at")
        serializer = UserSerializer(users, many=True)
        self.logger.info(f"Admin {request.user.email} retrieved user list.")
        return self.success(
            message="사용자 목록 조회에 성공했습니다.",
            data=serializer.data,
        )


class UserProfileView(BaseResponseMixin, APIView):
    """
    사용자 프로필 API.

    현재 로그인한 사용자의 프로필을 조회하고 수정할 수 있는 API입니다.
    """

    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    logger = logging.getLogger("apps")

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
        self.logger.info(f"User {request.user.email} retrieved profile.")
        return self.success(
            message=PROFILE_RETRIEVE_RESPONSE["message"],
            data=serializer.data,
            code=PROFILE_RETRIEVE_RESPONSE["code"],
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
            self.logger.info(f"User {request.user.email} updated profile successfully.")
            return self.success(
                message=PROFILE_UPDATE_RESPONSE["message"],
                data=serializer.data,
                code=PROFILE_UPDATE_RESPONSE["code"],
            )
        except IntegrityError as e:
            if "nickname" in str(e):
                self.logger.warning(
                    f"Profile update failed due to duplicate nickname for user {request.user.email}: {serializer.validated_data.get('nickname')}",
                )
                raise DuplicateNicknameError() from e
            else:
                self.logger.error(
                    f"Database integrity error during profile update for user {request.user.email}: {e}", exc_info=True
                )
                raise ServerError() from e
        except ValidationError as e:
            self.logger.warning(
                f"Profile update failed due to validation error for user {request.user.email}: {e.detail}",
                exc_info=True,
            )
            return self.error(message=INVALID_PROFILE_UPDATE["message"], data=e.detail)
        except Exception as e:
            self.logger.error(
                f"Unexpected error during profile update for user {request.user.email}: {e}", exc_info=True
            )
            raise ServerError() from e

    def patch(self, request):
        # PATCH는 put과 동일하게 partial update
        serializer = ProfileUpdateSerializer(request.user, data=request.data, partial=True)
        try:
            serializer.is_valid(raise_exception=True)
            serializer.save()
            self.logger.info(f"User {request.user.email} updated profile successfully (PATCH).")
            return self.success(
                message=PROFILE_UPDATE_RESPONSE["message"],
                data=serializer.data,
                code=PROFILE_UPDATE_RESPONSE["code"],
            )
        except IntegrityError as e:
            if "nickname" in str(e):
                self.logger.warning(
                    f"Profile update failed due to duplicate nickname for user {request.user.email}: {serializer.validated_data.get('nickname')}",
                )
                raise DuplicateNicknameError() from e
            else:
                self.logger.error(
                    f"Database integrity error during profile update for user {request.user.email}: {e}", exc_info=True
                )
                raise ServerError() from e
        except ValidationError as e:
            self.logger.warning(
                f"Profile update failed due to validation error for user {request.user.email}: {e.detail}",
                exc_info=True,
            )
            return self.error(message=INVALID_PROFILE_UPDATE["message"], data=e.detail)
        except Exception as e:
            self.logger.error(
                f"Unexpected error during profile update for user {request.user.email}: {e}", exc_info=True
            )
            raise ServerError() from e

    def delete(self, request):
        # 프로필 비활성화(soft delete)
        user = request.user
        user.is_active = False
        user.save(update_fields=["is_active"])
        self.logger.info(f"User {user.email} deactivated their profile.")
        return self.success(
            message="프로필이 비활성화되었습니다.",
            data=None,
            code=PROFILE_UPDATE_RESPONSE["code"],
        )


class NicknameCheckView(APIView):
    """닉네임 중복 체크 API"""

    permission_classes = [AllowAny]
    throttle_classes = [LoginAttemptThrottle]

    @swagger_auto_schema(
        operation_summary="닉네임 중복 체크",
        operation_description="닉네임의 중복 여부를 체크합니다",
        request_body=NicknameCheckSerializer,
        responses={
            200: openapi.Response(
                description="닉네임 사용 가능",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "code": openapi.Schema(type=openapi.TYPE_INTEGER, example=200),
                        "message": openapi.Schema(type=openapi.TYPE_STRING, example="사용 가능한 닉네임입니다."),
                        "data": openapi.Schema(type=openapi.TYPE_OBJECT, example=None),
                    },
                ),
            ),
            400: openapi.Response(
                description="닉네임 중복",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "code": openapi.Schema(type=openapi.TYPE_INTEGER, example=400),
                        "message": openapi.Schema(type=openapi.TYPE_STRING, example=DUPLICATE_NICKNAME["message"]),
                        "data": openapi.Schema(type=openapi.TYPE_OBJECT, example=None),
                    },
                ),
            ),
        },
    )
    def post(self, request):
        serializer = NicknameCheckSerializer(data=request.data)
        if serializer.is_valid():
            return self.success("사용 가능한 닉네임입니다.")
        return Response(
            {"code": 400, "message": serializer.errors["nickname"][0], "data": None}, status=status.HTTP_400_BAD_REQUEST
        )


# 예시: User 리스트에서 주문 수 집계 및 필요한 필드만 조회
# qs = User.objects.prefetch_related('orders').annotate(order_count=Count('orders')).only('id', 'email', 'nickname')

# 쿼리 로그/실행계획 확인 예시 (개발 환경에서만)
# from django.db import connection
# print(connection.queries)
# qs = User.objects.all()
# print(qs.explain())
